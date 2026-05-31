import os
import pandas as pd
import osmnx as ox
import networkx as nx
from nextbike_processing.database import get_connection, fetch_cached_routes, insert_routes, insert_trips
from nextbike_processing.utils import save_gzipped_geojson
from nextbike_processing.cities import get_city_coordinates_from_database
from geopy.distance import geodesic


def fetch_trip_data(city_id, date):
    query = f"""
        WITH ordered_bikes AS (
            SELECT *
            FROM public.bikes
            WHERE city_id = {city_id}
            AND DATE(last_updated) = '{date}'
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
        df = pd.read_sql_query(query, conn)
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])
    df["duration"] = df["end_time"] - df["start_time"]
    return df


def calculate_shortest_path(G, start_lat, start_lon, end_lat, end_lon):
    start_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    end_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

    if start_node not in G.nodes or end_node not in G.nodes:
        raise ValueError(f"Start or end node not in graph: {start_node}, {end_node}")

    try:
        shortest_path_length = nx.shortest_path_length(
            G, start_node, end_node, weight="length"
        )
        shortest_path = nx.shortest_path(G, start_node, end_node, weight="length")
    except nx.NetworkXNoPath:
        print(f"No path found between {start_node} and {end_node}")
        shortest_path_length = 0
        shortest_path = []
        return shortest_path_length, shortest_path

    path_segments = [[G.nodes[node]["y"], G.nodes[node]["x"]] for node in shortest_path]

    return shortest_path_length, path_segments


def build_coordinates_and_timestamps(trips):
    """
    Converts segments into GeoJSON-ordered coordinates [[lon, lat], ...]
    and a parallel timestamps array [iso_str, ...].
    """

    def process_row(row):
        start_time = pd.to_datetime(row["start_time"])
        duration = row["duration"]
        segments = row["segments"]
        num_segments = len(segments)
        time_increment = duration / max(num_segments - 1, 1)

        coordinates = [[lon, lat] for lat, lon in segments]
        timestamps = [
            (start_time + pd.to_timedelta(i * time_increment, unit="s")).isoformat()
            for i in range(num_segments)
        ]
        return pd.Series({"coordinates": coordinates, "timestamps": timestamps})

    result = trips.apply(process_row, axis=1)
    trips["coordinates"] = result["coordinates"]
    trips["timestamps"] = result["timestamps"]
    return trips


def remove_gps_errors(trips, meter_threshold=60):
    """
    Removes trips < 1 minute and moved less than meter_threshold.

    Parameters:
        trips (pd.DataFrame):
                Contains trip data with start_latitude, start_longitude,
                end_latitude, end_longitude, and duration columns.
        meter_threshold (int):
                Minimum distance in meters to consider a trip valid.

    Returns:
        pd.DataFrame: Filtered DataFrame with GPS errors removed
    """

    def is_valid_trip(row):
        # more than 60 seconds:
        # The minutes in teh dataset don't align on a full minute
        # For example: 01:18:42 --> 01:19:43
        duration_seconds = 62
        if row["duration"] <= duration_seconds:
            distance = geodesic(
                (row["start_latitude"], row["start_longitude"]),
                (row["end_latitude"], row["end_longitude"]),
            ).meters
            return distance >= meter_threshold
        return True

    filtered_trips = trips[trips.apply(is_valid_trip, axis=1)]

    return filtered_trips


def process_and_save_trips(city_id, date, folder, export_files=False):
    trips = fetch_trip_data(city_id, date)
    trips["start_time"] = trips["start_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    trips["end_time"] = trips["end_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    trips["duration"] = trips["duration"].dt.total_seconds()

    trips = remove_gps_errors(trips)

    unique_pairs = trips[["start_latitude", "start_longitude", "end_latitude", "end_longitude"]].drop_duplicates()

    with get_connection() as conn:
        cached_routes = fetch_cached_routes(unique_pairs, conn)

    if cached_routes.empty:
        uncached_pairs = unique_pairs
    else:
        uncached_pairs = unique_pairs.merge(
            cached_routes[["start_latitude", "start_longitude", "end_latitude", "end_longitude"]],
            on=["start_latitude", "start_longitude", "end_latitude", "end_longitude"],
            how="left",
            indicator=True,
        ).query('_merge == "left_only"').drop(columns=["_merge"])

    new_routes = pd.DataFrame()
    if not uncached_pairs.empty:
        city_lat, city_lng = get_city_coordinates_from_database(city_id)
        G = ox.graph_from_point((city_lat, city_lng), dist=10000, network_type="bike")

        route_results = []
        for _, row in uncached_pairs.iterrows():
            distance, segments = calculate_shortest_path(
                G, row["start_latitude"], row["start_longitude"],
                row["end_latitude"], row["end_longitude"]
            )
            route_results.append({
                "start_latitude": row["start_latitude"],
                "start_longitude": row["start_longitude"],
                "end_latitude": row["end_latitude"],
                "end_longitude": row["end_longitude"],
                "distance": distance,
                "segments": segments,
            })
        new_routes = pd.DataFrame(route_results)

        with get_connection() as conn:
            insert_routes(new_routes, conn)

    all_routes = pd.concat(
        [df for df in [cached_routes, new_routes] if not df.empty],
        ignore_index=True,
    )

    trips = trips.merge(
        all_routes[["start_latitude", "start_longitude", "end_latitude", "end_longitude", "distance", "segments"]],
        on=["start_latitude", "start_longitude", "end_latitude", "end_longitude"],
        how="left",
    )

    trips = build_coordinates_and_timestamps(trips)

    with get_connection() as conn:
        insert_trips(trips, city_id, conn)

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
                "timestamps": row["timestamps"],
            },
        }
        for _, row in trips.iterrows()
    ]

    geojson = {"type": "FeatureCollection", "features": features}
    if export_files:
        save_gzipped_geojson(os.path.join(folder, f"{city_id}_trips_{date}.geojson.gz"), geojson)
