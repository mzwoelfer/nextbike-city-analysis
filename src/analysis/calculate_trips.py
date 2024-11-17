import json
import psycopg
import pandas as pd
import osmnx as ox
import networkx as nx
import config
import os


def get_trip_data():
    with psycopg.connect(
        host=config.dbhost,
        dbname=config.dbname,
        user=config.dbuser,
        password=config.dbpassword,
    ) as conn:
        query_bike_movements = """
        WITH bike_movements AS (
            SELECT bike_number,
                   latitude AS start_latitude,
                   longitude AS start_longitude,
                   last_updated AS start_time,
                   LEAD(latitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_latitude,
                   LEAD(longitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_longitude,
                   LEAD(last_updated) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_time
            FROM public.bikes
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
        ORDER BY bike_number, start_time
        LIMIT 50;
        """

        df = pd.read_sql_query(query_bike_movements, conn)

    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])

    df["duration"] = df["end_time"] - df["start_time"]
    return df


def save_files_by_day(date, group):
    trips_json = group.to_dict(orient="records")
    json_file = os.path.join(f"trips_{date}.json")

    print(trips_json)
    with open(json_file, "w") as f:
        json.dump(trips_json, f, indent=4)

    csv_file = os.path.join(f"trips_{date}.csv")
    group.to_csv(csv_file, index=False)


def calculate_shortest_path(G, start_lat, start_lon, end_lat, end_lon):
    start_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    end_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

    shortest_path_length = nx.shortest_path_length(
        G, start_node, end_node, weight="length"
    )

    shortest_path = nx.shortest_path(G, start_node, end_node, weight="length")
    path_segments = [[G.nodes[node]["y"], G.nodes[node]["x"]] for node in shortest_path]

    return shortest_path_length, path_segments


def main():
    southwest_lat, southwest_lon = 50.52289, 8.60267
    northeast_lat, northeast_lon = 50.63589, 8.74256

    bbox = (northeast_lat, southwest_lat, northeast_lon, southwest_lon)
    G = ox.graph_from_bbox(*bbox, network_type="bike")

    trips = get_trip_data()

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

    save_files_by_day("", trips)


if __name__ == "__main__":
    main()
