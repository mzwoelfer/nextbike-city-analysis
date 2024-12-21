import os
import pandas as pd
import osmnx as ox
import networkx as nx
from nextbike_processing.database import get_connection
from nextbike_processing.utils import save_json, save_csv


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
    path = nx.shortest_path(G, start_node, end_node, weight="length")
    return path


def process_and_save_trips(city_id, date, folder):
    trips = fetch_trip_data(city_id, date)
    trips["date"] = trips["start_time"].dt.date
    G = ox.graph_from_point(
        (trips["start_latitude"].iloc[0], trips["start_longitude"].iloc[0]), dist=10000
    )

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
    trips["path"] = results
    trips["start_time"] = trips["start_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    trips["end_time"] = trips["end_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    save_json(
        os.path.join(folder, f"{city_id}_trips_{date}.json"),
        trips.to_dict(orient="records"),
    )
    save_csv(os.path.join(folder, f"{city_id}_trips_{date}.csv"), trips)
