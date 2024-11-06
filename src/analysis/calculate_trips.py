import psycopg
import pandas as pd
import osmnx as ox
import networkx as nx
import config


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
        ORDER BY bike_number, start_time;
        """

        # Execute the query and fetch the data into a DataFrame
        df = pd.read_sql_query(query_bike_movements, conn)

    df["duration"] = df["end_time"] - df["start_time"]
    return df


def calculate_shortest_path(G, start_lat, start_lon, end_lat, end_lon):
    start_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    end_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

    shortest_path_length = nx.shortest_path_length(
        G, start_node, end_node, weight="length"
    )
    return shortest_path_length


def main():
    G = ox.graph_from_place("Gießen, Germany", network_type="bike")

    trips = get_trip_data()

    trips["distance"] = trips.apply(
        lambda row: calculate_shortest_path(
            G,
            row["start_latitude"],
            row["start_longitude"],
            row["end_latitude"],
            row["end_longitude"],
        ),
        axis=1,
    )

    print(
        trips[
            [
                "bike_number",
                "start_latitude",
                "start_longitude",
                "start_time",
                "end_latitude",
                "end_longitude",
                "end_time",
                "duration",
                "distance",
            ]
        ]
    )


if __name__ == "__main__":
    main()
