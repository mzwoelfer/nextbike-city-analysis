import os
import pandas as pd
import osmnx as ox
import networkx as nx
from nextbike_processing.database import get_connection
from nextbike_processing.utils import save_gzipped_csv, save_json, save_csv
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


def add_timestamps_to_segments(trips):
    """
    Adds timestamps to each segment in the DataFrame's segments column.
    Uses existing start_time, end_time, and duration.
    """

    def add_timestamps(row):
        start_time = pd.to_datetime(row["start_time"])
        duration = row["duration"]

        num_segments = len(row["segments"])
        time_increment = duration / max(num_segments - 1, 1)  # Avoid division by zero

        segments_with_timestamps = []
        for i, segment in enumerate(row["segments"]):
            timestamp = start_time + pd.to_timedelta(i * time_increment, unit="s")
            segments_with_timestamps.append(segment + [timestamp.isoformat()])

        return segments_with_timestamps

    trips["segments"] = trips.apply(add_timestamps, axis=1)
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


def process_and_save_trips(city_id, date, folder):
    trips = fetch_trip_data(city_id, date)
    city_lat, city_lng = get_city_coordinates_from_database(city_id)

    G = ox.graph_from_point((city_lat, city_lng), dist=10000, network_type="bike")

    trips["date"] = trips["start_time"].dt.date.astype(str)
    trips["start_time"] = trips["start_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    trips["end_time"] = trips["end_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    trips["duration"] = trips["duration"].dt.total_seconds()

    trips = remove_gps_errors(trips)

    results = trips.apply(
        lambda row: calculate_shortest_path(
            G,
            row["start_latitude"],
            row["start_longitude"],
            row["end_latitude"],
            row["end_longitude"],
        ),
        axis=1,
    )

    trips["distance"], trips["segments"] = zip(*results)

    trips = add_timestamps_to_segments(trips)

    save_gzipped_csv(os.path.join(folder, f"{city_id}_trips_{date}.csv.gz"), trips)
