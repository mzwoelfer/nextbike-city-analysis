import json
import pandas as pd
import psycopg
from nextbike_processing.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_connection():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def get_uncached_route_pairs(unique_pairs, conn):
    """
    Find which route pairs are NOT yet cached in the database.
    
    This avoids expensive re-computation of routes we've already calculated.
    Routes are identified by their (start_lat, start_lon, end_lat, end_lon) tuple.
    
    Args:
        unique_pairs (pd.DataFrame): DataFrame with columns:
            [start_latitude, start_longitude, end_latitude, end_longitude]
            These are the O/D (origin/destination) pairs we want to route.
        
        conn (psycopg.Connection): Active database connection
    
    Returns:
        pd.DataFrame: Subset of unique_pairs that are NOT in public.routes table.
                     Empty DataFrame if all pairs are cached.
    
    Example:
        unique_pairs = pd.DataFrame({
            'start_latitude': [48.2, 48.3],
            'start_longitude': [16.3, 16.4],
            'end_latitude': [48.25, 48.35],
            'end_longitude': [16.35, 16.45],
        })
        uncached = get_uncached_route_pairs(unique_pairs, conn)
        # Returns only pairs not in routes table
    """
    if unique_pairs.empty:
        return unique_pairs.copy()
    
    # Build list of coordinate tuples
    pairs_list = [
        (float(r.start_latitude), float(r.start_longitude), 
         float(r.end_latitude), float(r.end_longitude))
        for _, r in unique_pairs.iterrows()
    ]
    
    # Create SQL VALUES clause for each pair
    # E.g., VALUES (48.2, 16.3, 48.25, 16.35), (48.3, 16.4, 48.35, 16.45)
    placeholders = ", ".join(["(%s, %s, %s, %s)"] * len(pairs_list))
    params = [v for pair in pairs_list for v in pair]
    
    with conn.cursor() as cur:
        # Use EXCEPT to find pairs NOT in database
        # Think of it like: "Give me all the pairs I asked for, EXCEPT the ones already cached"
        cur.execute(
            f"""
            SELECT * FROM (VALUES {placeholders})
            AS requested(start_lat, start_lon, end_lat, end_lon)
            EXCEPT
            SELECT start_latitude, start_longitude, end_latitude, end_longitude
            FROM public.routes
            """,
            params,
        )
        uncached_rows = cur.fetchall()
    
    if not uncached_rows:
        return pd.DataFrame(columns=unique_pairs.columns)
    
    # Convert back to DataFrame with original column names
    df = pd.DataFrame(
        uncached_rows,
        columns=["start_latitude", "start_longitude", "end_latitude", "end_longitude"],
    )
    return df


def get_cached_routes(unique_pairs, conn):
    """
    Retrieve routing information for pairs that ARE already cached in the database.
    
    This is the "happy path" - routes we've already computed and stored.
    Returns complete route information including coordinates and distance.
    
    Args:
        unique_pairs (pd.DataFrame): DataFrame with columns:
            [start_latitude, start_longitude, end_latitude, end_longitude]
            These are the O/D pairs to look up in the cache.
        
        conn (psycopg.Connection): Active database connection
    
    Returns:
        pd.DataFrame: Routes found in cache with columns:
            [start_latitude, start_longitude, end_latitude, end_longitude, distance, segments]
            
            Where:
            - distance: distance in meters (float)
            - segments: list of [lat, lon] coordinate pairs representing the route path
        
        Returns empty DataFrame if no routes found in cache.
    
    Example:
        cached = get_cached_routes(unique_pairs, conn)
        # Returns something like:
        # | start_latitude | start_longitude | ... | distance | segments           |
        # | 48.2           | 16.3            | ... | 2500.5   | [[48.21, 16.31]...] |
    """
    empty = pd.DataFrame(
        columns=["start_latitude", "start_longitude", "end_latitude", "end_longitude", "distance", "segments"]
    )
    
    if unique_pairs.empty:
        return empty
    
    # Build list of coordinate tuples
    pairs_list = [
        (float(r.start_latitude), float(r.start_longitude), 
         float(r.end_latitude), float(r.end_longitude))
        for _, r in unique_pairs.iterrows()
    ]
    
    # Create SQL VALUES clause
    placeholders = ", ".join(["(%s, %s, %s, %s)"] * len(pairs_list))
    params = [v for pair in pairs_list for v in pair]
    
    with conn.cursor() as cur:
        # Query the routes table for matching O/D pairs
        cur.execute(
            f"""
            SELECT 
                start_latitude, start_longitude, 
                end_latitude, end_longitude,
                distance_meters, 
                coordinates
            FROM public.routes
            WHERE (start_latitude, start_longitude, end_latitude, end_longitude)
            IN (VALUES {placeholders})
            """,
            params,
        )
        rows = cur.fetchall()
    
    if not rows:
        return empty
    
    df = pd.DataFrame(
        rows,
        columns=["start_latitude", "start_longitude", "end_latitude", "end_longitude", "distance_meters", "coordinates"],
    )
    
    # Database stores coordinates in GeoJSON order: [lon, lat]
    # Convert to internal format: [lat, lon] for easier computation
    df["segments"] = df["coordinates"].apply(
        lambda coords: [[lat, lon] for lon, lat in coords]
    )
    
    # Rename to match expected column names
    df = df.rename(columns={"distance_meters": "distance"})
    
    return df[["start_latitude", "start_longitude", "end_latitude", "end_longitude", "distance", "segments"]]


def insert_new_routes(routes_df, conn):
    """
    Store newly computed routes in the database cache.
    
    This is the "write" operation after we've computed new routes using OSM/pathfinding.
    Silently skips routes that already exist (ON CONFLICT DO NOTHING).
    
    Args:
        routes_df (pd.DataFrame): DataFrame with columns:
            [start_latitude, start_longitude, end_latitude, end_longitude, distance, segments]
            
            Where:
            - distance: distance in meters (float)
            - segments: list of [lat, lon] coordinate pairs representing the route path
        
        conn (psycopg.Connection): Active database connection (must have commit capability)
    
    Returns:
        None (commits to database)
    
    Example:
        new_routes = pd.DataFrame({
            'start_latitude': [48.2],
            'start_longitude': [16.3],
            'end_latitude': [48.25],
            'end_longitude': [16.35],
            'distance': [2500.5],
            'segments': [[[48.21, 16.31], [48.22, 16.32], ...]]
        })
        insert_new_routes(new_routes, conn)
    """
    with conn.cursor() as cur:
        for _, row in routes_df.iterrows():
            if not row["segments"]:
                # Skip routes with no path data
                continue
            
            # Convert internal format [lat, lon] to GeoJSON format [lon, lat] for storage
            geojson_coordinates = [[lon, lat] for lat, lon in row["segments"]]
            
            # Insert or ignore if this exact route already exists
            cur.execute(
                """
                INSERT INTO public.routes
                    (start_latitude, start_longitude, end_latitude, end_longitude, distance_meters, coordinates)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (start_latitude, start_longitude, end_latitude, end_longitude) 
                DO NOTHING
                """,
                (
                    row["start_latitude"], 
                    row["start_longitude"],
                    row["end_latitude"], 
                    row["end_longitude"],
                    row["distance"],
                    json.dumps(geojson_coordinates),
                ),
            )
    
    conn.commit()


def insert_trips(trips_df, city_id, conn):
    """
    Batch insert trip records with their associated routes.
    
    A "trip" is a bike movement from point A to point B with timestamps.
    This function links each trip to its pre-computed route (via START/END coordinates).
    
    Args:
        trips_df (pd.DataFrame): DataFrame with columns:
            [bike_number, start_time, end_time, duration, 
             start_latitude, start_longitude, end_latitude, end_longitude,
             timestamps, coordinates]
        
        city_id (int): The city being processed
        conn (psycopg.Connection): Active database connection
    
    Returns:
        None (commits to database)
    
    Notes:
        - Silently skips duplicate trips (same bike, city, start_time)
        - Looks up route_id from coordinates (foreign key to routes table)
    """
    if trips_df.empty:
        return
    
    with conn.cursor() as cur:
        records = [
            (
                row["bike_number"], 
                city_id,
                row["start_time"], 
                row["end_time"], 
                row["duration"],
                row["start_latitude"], 
                row["start_longitude"],
                row["end_latitude"], 
                row["end_longitude"],
                json.dumps(row["timestamps"]),
            )
            for _, row in trips_df.iterrows()
        ]
        
        # Batch insert for performance
        # The subquery joins with routes table to get the route_id
        cur.executemany(
            """
            INSERT INTO public.trips
                (bike_number, city_id, start_time, end_time, duration_seconds, route_id, timestamps)
            SELECT %s, %s, %s::timestamp, %s::timestamp, %s,
                (SELECT id FROM public.routes
                 WHERE start_latitude = %s 
                   AND start_longitude = %s
                   AND end_latitude = %s 
                   AND end_longitude = %s
                 LIMIT 1),
                %s
            ON CONFLICT (bike_number, city_id, start_time) 
            DO NOTHING
            """,
            records,
        )
    
    conn.commit()