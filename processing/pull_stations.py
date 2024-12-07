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


def get_station_data_from_database(city_id):
    with psycopg.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password,
    ) as conn:
        query_stations = f"""
        WITH station_data AS (
            SELECT
                id,
                uid,
                latitude,
                longitude,
                name,
                spot,
                station_number,
                maintenance,
                terminal_type,
                last_updated,
                ROW_NUMBER() OVER (
                    PARTITION BY uid, latitude, longitude, name, spot, station_number, terminal_type, DATE(last_updated), maintenance
                    ORDER BY last_updated
                ) AS rn
            FROM public.stations
            WHERE city_id = {city_id}
        ),
        filtered_data AS (
            SELECT
                *
            FROM station_data
            WHERE rn = 1
        )
        SELECT
            id,
            uid,
            latitude,
            longitude,
            name,
            spot,
            station_number,
            maintenance,
            terminal_type,
            last_updated
        FROM filtered_data
        ORDER BY uid, last_updated;
        """

        df = pd.read_sql_query(query_stations, conn)

    df["date"] = df["last_updated"].dt.date.astype(str)
    df["last_updated"] = df["last_updated"].dt.strftime("%Y-%m-%dT%H:%M:%S")

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
        stations = get_station_data_from_database(args.city_id)

    print(stations)

    grouped = stations.groupby("date")
    for date, group in grouped:
        save_files_by_day(date, stations, args.export_folder, args.city_id)


if __name__ == "__main__":
    main()
