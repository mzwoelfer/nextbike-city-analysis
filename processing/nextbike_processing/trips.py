import os
import pandas as pd
import osmnx as ox
import networkx as nx
from nextbike_processing.database import (
    get_connection, 
    get_cached_routes,
    get_uncached_route_pairs,
    insert_new_routes, 
    insert_trips
)
from nextbike_processing.utils import save_gzipped_geojson, save_gzipped_csv
from nextbike_processing.cities import get_city_coordinates_from_database


def fetch_trip_data(city_id, date):
    """
    Load raw bike movements for a specific day.
    
    A "movement" is detected when a bike is seen at one location, then later
    seen at a different location. This function reconstructs those movements
    from the bikes table.
    
    Args:
        city_id (int): City to query
        date (str): Date in YYYY-MM-DD format
    
    Returns:
        pd.DataFrame with columns:
            [bike_number, start_latitude, start_longitude, start_time,
             end_latitude, end_longitude, end_time, duration]
        
        Where duration is a timedelta object (will be converted to seconds later)
    """
    query = """
        WITH ordered_bikes AS (
            SELECT *
            FROM public.bikes
            WHERE city_id = %s
            AND DATE(last_updated) = %s
            ORDER BY bike_number, last_updated
        ),
        bike_movements AS (
            SELECT bike_number,
                   latitude AS start_latitude,
                   longitude AS start_longitude,
                   last_updated AS start_time,
                   LEAD(latitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_latitude,
                   LEAD(longitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_longitude,
                   LEAD(last_updated) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_time
            FROM ordered_bikes
        )
        SELECT bike_number,
               start_latitude,
               start_longitude,
               start_time,
               end_latitude,
               end_longitude,
               end_time
        FROM bike_movements
        WHERE end_latitude IS NOT NULL
          AND (start_latitude != end_latitude OR start_longitude != end_longitude)
        ORDER BY start_time, bike_number;
    """
    
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=(city_id, date))
    
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])
    df["duration"] = df["end_time"] - df["start_time"]
    
    return df


def calculate_shortest_path(G, start_lat, start_lon, end_lat, end_lon):
    """
    Compute the shortest bike-friendly route between two points using OSM graph.
    
    Uses the street network graph to find the most direct bike route,
    returning the distance and the coordinate sequence.
    
    Args:
        G (networkx.MultiDiGraph): OSM street network graph (from osmnx)
        start_lat, start_lon (float): Starting point coordinates
        end_lat, end_lon (float): Ending point coordinates
    
    Returns:
        tuple: (distance_meters, segments)
            - distance_meters (float): Total distance along the route
            - segments (list): [[lat, lon], [lat, lon], ...] coordinate sequence
            
        Returns (None, []) if route cannot be computed
    """
    try:
        # Find closest street intersection nodes to our start/end points
        start_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
        end_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

        if start_node not in G.nodes or end_node not in G.nodes:
            return None, []

        # Compute shortest path
        shortest_path_length = nx.shortest_path_length(
            G, start_node, end_node, weight="length"
        )
        shortest_path = nx.shortest_path(G, start_node, end_node, weight="length")
        
    except nx.NetworkXNoPath:
        # No route exists between these points
        return None, []
    except Exception:
        # Unexpected error
        return None, []

    # Convert node IDs to [lat, lon] coordinates
    path_segments = [[G.nodes[node]["y"], G.nodes[node]["x"]] for node in shortest_path]

    return shortest_path_length, path_segments

def process_and_save_trips(city_id, date, folder, export_files=False):
    """
    Main orchestration function: Fetch raw movements → compute routes → save results.
    
    This is the high-level flow:
    1. Load raw bike movements from database
    2. Identify which O/D pairs need routing (not cached)
    3. Compute routes for uncached pairs
    4. Combine with cached routes
    5. Interpolate timestamps along routes
    6. Save to database and optionally export files
    
    Args:
        city_id (int): City to process
        date (str): Date in YYYY-MM-DD format
        folder (str): Export folder path (if export_files=True)
        export_files (bool): Whether to export .geojson.gz and .csv.gz files
    
    Returns:
        None (all data saved to database)
    """
    
    # ===== STEP 1: Fetch raw bike movements =====
    print(f"[{date}] Fetching trip data for city {city_id}...")
    trips = fetch_trip_data(city_id, date)
    
    # Convert duration to seconds (for storage)
    trips["duration"] = trips["duration"].dt.total_seconds()
    
    # Get unique O/D pairs from all trips
    # (Many trips use the same start→end locations, so we cache routes)
    unique_pairs = trips[
        ["start_latitude", "start_longitude", "end_latitude", "end_longitude"]
    ].drop_duplicates()
    
    print(f"  Found {len(trips)} trips from {len(unique_pairs)} unique routes")
    
    # ===== STEP 2: Check database for cached routes =====
    print(f"  Checking database for cached routes...")
    with get_connection() as conn:
        cached_routes = get_cached_routes(unique_pairs, conn)
        uncached_pairs = get_uncached_route_pairs(unique_pairs, conn)
    
    print(f"    Cached: {len(cached_routes)} routes")
    print(f"    Need to compute: {len(uncached_pairs)} routes")
    
    # ===== STEP 3: Compute routes for uncached pairs =====
    new_routes = pd.DataFrame()
    if not uncached_pairs.empty:
        print(f"  Computing {len(uncached_pairs)} new routes using OSM...")
        
        # Load city center and build street network graph
        city_lat, city_lng = get_city_coordinates_from_database(city_id)
        G = ox.graph_from_point((city_lat, city_lng), dist=10000, network_type="bike")
        
        route_results = []
        for idx, (_, row) in enumerate(uncached_pairs.iterrows(), 1):
            if idx % 50 == 0:
                print(f"    Progress: {idx}/{len(uncached_pairs)}")
            
            distance, segments = calculate_shortest_path(
                G, 
                row["start_latitude"], row["start_longitude"],
                row["end_latitude"], row["end_longitude"]
            )
            
            # Only store if we got a valid route
            if segments:
                route_results.append({
                    "start_latitude": row["start_latitude"],
                    "start_longitude": row["start_longitude"],
                    "end_latitude": row["end_latitude"],
                    "end_longitude": row["end_longitude"],
                    "distance": distance,
                    "segments": segments,
                })
        
        new_routes = pd.DataFrame(route_results)
        print(f"  Successfully computed {len(new_routes)} routes")
        
        # Save to database for next time
        with get_connection() as conn:
            insert_new_routes(new_routes, conn)
            print(f"  Cached new routes in database")
    
    # ===== STEP 4: Combine cached + newly computed routes =====
    all_routes_list = [df for df in [cached_routes, new_routes] if not df.empty]
    if not all_routes_list:
        print(f"  WARNING: No routes available!")
        return
    
    all_routes = pd.concat(all_routes_list, ignore_index=True)
    
    # ===== STEP 5: Join route info back to trips =====
    trips = trips.merge(
        all_routes[
            ["start_latitude", "start_longitude", "end_latitude", "end_longitude", 
             "distance", "segments"]
        ],
        on=["start_latitude", "start_longitude", "end_latitude", "end_longitude"],
        how="left",
    )
    
    # ===== STEP 6: Save to database =====
    print(f"  Saving {len(trips)} trips to database...")
    with get_connection() as conn:
        insert_trips(trips, city_id, conn)
    print(f"  Done!")
    
    # ===== STEP 7: Export files (optional) =====
    if not export_files:
        return
    
    print(f"  Exporting files...")
    
    # Export as GeoJSON for web mapping
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": row["coordinates"],
            },
            "properties": {
                "bike_number": row["bike_number"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "duration": row["duration"],
                "distance": row["distance"],
            },
        }
        for _, row in trips.iterrows()
    ]

    geojson = {"type": "FeatureCollection", "features": features}
    save_gzipped_geojson(
        os.path.join(folder, f"{city_id}_trips_{date}.geojson.gz"), 
        geojson
    )
    
    # Export as CSV for static visualization (GitHub Pages mode)
    trips_export = trips.copy()
    trips_export["date"] = date
    # Convert [lon, lat] coordinates to [lat, lon, timestamp] for CSV storage
    trips_export["segments"] = trips_export.apply(
        lambda row: [[lat, lon] for [lon, lat] in row["coordinates"]],
        axis=1,
    )
    
    trips_export["route_id"] = trips_export.groupby(
        ["start_latitude", "start_longitude", "end_latitude", "end_longitude"]
    ).ngroup()
    csv_cols = [
        "bike_number", "start_latitude", "start_longitude", "start_time",
        "end_latitude", "end_longitude", "end_time", "duration", "date",
        "distance", "segments", "route_id"
    ]
    save_gzipped_csv(
        os.path.join(folder, f"{city_id}_trips_{date}.csv.gz"), 
        trips_export[csv_cols]
    )
    print(f"  Exported geojson and csv files")