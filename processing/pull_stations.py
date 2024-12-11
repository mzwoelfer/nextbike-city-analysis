import json
import pandas as pd
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


def get_station_data_from_database(city_id, date):
    with psycopg.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password,
    ) as conn:
        query_stations = f"""
        WITH station_data AS (
            SELECT
                id, uid, latitude, longitude, name, spot, station_number, maintenance, terminal_type, city_id, city_name,
                ROW_NUMBER() OVER (
                    PARTITION BY uid, latitude, longitude, name, spot, station_number, terminal_type, DATE(last_updated), maintenance
                    ORDER BY last_updated DESC
                ) AS rn
            FROM public.stations
            WHERE city_id = {city_id}
            AND DATE(last_updated) = '{date}'
        ),
        filtered_stations AS (
            SELECT
                id, uid, latitude, longitude, name, spot, station_number, maintenance, terminal_type, city_id, city_name
            FROM station_data
            WHERE rn = 1
        ),
        bike_data AS (
            SELECT
                DATE_TRUNC('minute', b.last_updated) AS minute,
                b.station_number,
                COUNT(b.bike_number) AS bike_count,
                STRING_AGG(b.bike_number::TEXT, ', ') AS bike_list
            FROM
                public.bikes b
            WHERE
                city_id = {city_id}
                AND DATE(b.last_updated) = '{date}'
            GROUP BY
                DATE_TRUNC('minute', b.last_updated), b.station_number
        ),
        distinct_minutes AS (
            SELECT DISTINCT DATE_TRUNC('minute', b.last_updated) AS minute
            FROM public.bikes b
            WHERE
                city_id = {city_id}
                AND DATE(b.last_updated) = '{date}'
        ),
        station_minute_combinations AS (
            SELECT
                dm.minute,
                fs.id,
                fs.uid,
                fs.latitude,
                fs.longitude,
                fs.name,
                fs.spot,
                fs.station_number,
                fs.maintenance,
                fs.terminal_type,
                fs.city_id,
                fs.city_name
            FROM
                distinct_minutes dm
            CROSS JOIN
                filtered_stations fs
        )
        SELECT
            smc.minute,
            smc.id,
            smc.uid,
            smc.latitude,
            smc.longitude,
            smc.name,
            smc.spot,
            smc.station_number,
            smc.maintenance,
            smc.terminal_type,
            smc.city_id,
            smc.city_name,
            COALESCE(bd.bike_count, 0) AS bike_count,
            COALESCE(bd.bike_list, '') AS bike_list
        FROM
            station_minute_combinations smc
        LEFT JOIN
            bike_data bd
        ON
            smc.station_number = bd.station_number
            AND smc.minute = bd.minute
        ORDER BY
            smc.minute, smc.station_number;
        """

        df = pd.read_sql_query(query_stations, conn)

    df["minute"] = df["minute"].dt.strftime("%Y-%m-%dT%H:%M:%S")

    return df


def get_station_data_from_csv(file_path):
    df = pd.read_csv(file_path)
    df["date"] = df["last_updated"].dt.date

    return df


def save_files_by_day(date, group, folder, city_id):
    stations_json = group.to_dict(orient="records")
    json_file = os.path.join(folder, f"{city_id}_stations_{date}.json")

    with open(json_file, "w") as f:
        json.dump(stations_json, f, indent=4)

    csv_file = os.path.join(folder, f"{city_id}_stations_{date}.csv")
    group.to_csv(csv_file, index=False)


def main():
    parser = argparse.ArgumentParser(description="Pull station data from database")
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
        stations = get_station_data_from_csv(args.input_file)
    else:
        print("Fetching data from the database...")
        date = "2024-12-06"
        stations = get_station_data_from_database(args.city_id, date)

    print(stations)

    save_files_by_day(date, stations, args.export_folder, args.city_id)


if __name__ == "__main__":
    main()
