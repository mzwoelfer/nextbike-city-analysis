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


def fetch_cached_routes(unique_pairs, conn):
    """
    Fetch routes from the DB for the given O/D pairs.
    Returns a DataFrame with columns:
        start_latitude, start_longitude, end_latitude, end_longitude, distance, segments
    segments are [[lat, lon], ...] - internal format ready for build_coordinates_and_timestamps.
    """
    empty = pd.DataFrame(
        columns=["start_latitude", "start_longitude", "end_latitude", "end_longitude", "distance", "segments"]
    )
    if unique_pairs.empty:
        return empty

    pairs_list = [
        (float(r.start_latitude), float(r.start_longitude), float(r.end_latitude), float(r.end_longitude))
        for _, r in unique_pairs.iterrows()
    ]
    placeholders = ", ".join(["(%s, %s, %s, %s)"] * len(pairs_list))
    params = [v for pair in pairs_list for v in pair]

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT start_latitude, start_longitude, end_latitude, end_longitude,
                   distance_meters, coordinates
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
    # DB stores [lon, lat] (GeoJSON order) - convert back to internal [lat, lon]
    df["segments"] = df["coordinates"].apply(lambda coords: [[lat, lon] for lon, lat in coords])
    df = df.rename(columns={"distance_meters": "distance"})
    return df[["start_latitude", "start_longitude", "end_latitude", "end_longitude", "distance", "segments"]]


def insert_routes(routes_df, conn):
    """
    Insert new routes into the routes table. Skips existing routes silently.
    routes_df columns: start_latitude, start_longitude, end_latitude, end_longitude, distance, segments.
    segments are [[lat, lon], ...] - stored as [[lon, lat], ...] (GeoJSON order) in the DB.
    """
    with conn.cursor() as cur:
        for _, row in routes_df.iterrows():
            if not row["segments"]:
                continue
            coordinates = [[lon, lat] for lat, lon in row["segments"]]
            cur.execute(
                """
                INSERT INTO public.routes
                    (start_latitude, start_longitude, end_latitude, end_longitude, distance_meters, coordinates)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (start_latitude, start_longitude, end_latitude, end_longitude) DO NOTHING
                """,
                (
                    row["start_latitude"], row["start_longitude"],
                    row["end_latitude"], row["end_longitude"],
                    row["distance"],
                    json.dumps(coordinates),
                ),
            )
    conn.commit()


def insert_trips(trips_df, city_id, conn):
    """
    Batch insert trips for faster performance.
    Skips duplicates silently with ON CONFLICT.
    """
    if trips_df.empty:
        return
    
    with conn.cursor() as cur:
        records = [
            (
                row["bike_number"], city_id,
                row["start_time"], row["end_time"], row["duration"],
                row["start_latitude"], row["start_longitude"],
                row["end_latitude"], row["end_longitude"],
                json.dumps(row["timestamps"]),
            )
            for _, row in trips_df.iterrows()
        ]
        
        # Batch insert using COPY (much faster than row-by-row inserts)
        cur.executemany(
            """
            INSERT INTO public.trips
                (bike_number, city_id, start_time, end_time, duration_seconds, route_id, timestamps)
            SELECT %s, %s, %s::timestamp, %s::timestamp, %s,
                (SELECT id FROM public.routes
                 WHERE start_latitude = %s AND start_longitude = %s
                   AND end_latitude = %s AND end_longitude = %s),
                %s
            ON CONFLICT (bike_number, city_id, start_time) DO NOTHING
            """,
            records,
        )
    conn.commit()
