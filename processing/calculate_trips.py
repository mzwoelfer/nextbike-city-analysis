import json
import pandas as pd
import osmnx as ox
import networkx as nx
import argparse
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")


def get_trip_data_from_database(city_id):
    with psycopg.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password,
    ) as conn:
        query_bike_movements = f"""
        WITH ordered_bikes AS (
            SELECT *
            FROM public.bikes
            WHERE city_id = {city_id}
            AND DATE(last_updated) = '2024-12-06'
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

        df = pd.read_sql_query(query_bike_movements, conn)

    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])

    df["duration"] = df["end_time"] - df["start_time"]
    return df


def get_city_coordinates_from_database(city_id):
    with psycopg.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password,
    ) as conn:
        with conn.cursor() as cur:
            query_cities = f"""
            SELECT latitude, longitude
            FROM public.cities
            WHERE city_id = {city_id};
            """
            cur.execute(
                query_cities,
            )
            lat, long = cur.fetchone()

    return lat, long


def get_trip_data_from_csv(file_path):
    df = pd.read_csv(file_path)

    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])

    df["duration"] = df["end_time"] - df["start_time"]
    return df


def add_city_info_to_trips_json(city_lat, city_lng, trips_json):
    """
    Takes the trips as JSON.
    Returns an Object with city_info and trips
    """
    city_and_trips_json = {
        "city_info": {"lat": city_lat, "lng": city_lng},
        "trips": trips_json,
    }

    return city_and_trips_json


def save_files_by_day_json(date, city_and_trips_json, folder):
    json_file = os.path.join(folder, f"trips_{date}.json")

    with open(json_file, "w") as f:
        json.dump(city_and_trips_json, f, indent=4)


def save_files_by_day_csv(date, group, folder):
    """
    TBD.
    Export trips data including city info to a csv file
    """

    return


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


def main():
    parser = argparse.ArgumentParser(
        description="Calculate next bikebike trips and their distances from a CSV file or database."
    )
    parser.add_argument(
        "--city-id",
        type=int,
        required=True,
        help="The city_id to filter trips from the database",
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default=None,
        help="Path to the input CSV file. If not provided, data will be fetched from the database.",
    )
    parser.add_argument(
        "--export-folder",
        required=True,
        help="Folder to export the resulting JSON and CSV files (must exist).",
    )

    args = parser.parse_args()
    if not os.path.exists(args.export_folder):
        print(f"Error: Export folder ${args.export_folder} doesn't exist.")
        print(f"Error: Create the folder yourself or check your path")
        exit(1)

    if args.input_file:
        print(f"Loading data from {args.input_file}...")
        trips = get_trip_data_from_csv(args.input_file)
    else:
        print(f"Fetching nextbike data for city_id: {args.city_id} from the database")
        trips = get_trip_data_from_database(args.city_id)

    city_lat, city_lng = get_city_coordinates_from_database(args.city_id)
    city_coordinates = (city_lat, city_lng)
    G = ox.graph_from_point(
        city_coordinates, dist=10000, network_type="bike", simplify=True
    )

    trips["date"] = trips["start_time"].dt.date

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

    trips["start_time"] = trips["start_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    trips["end_time"] = trips["end_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    trips["duration"] = trips["duration"].dt.total_seconds()
    trips["date"] = trips["date"].astype(str)

    trips = add_timestamps_to_segments(trips)

    grouped = trips.groupby("date")
    for date, group in grouped:
        trips_json = group.to_dict(orient="records")
        city_and_trips_json = add_city_info_to_trips_json(
            city_lat, city_lng, trips_json
        )

        save_files_by_day_json(date, city_and_trips_json, args.export_folder)


if __name__ == "__main__":
    main()
