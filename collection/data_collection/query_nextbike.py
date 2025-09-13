import requests
import argparse
import datetime
import psycopg
import os
from dotenv import load_dotenv


db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")


class NextbikeAPI:
    """INteract with Nextbike API"""

    BASE_URL = "https://maps.nextbike.net/maps/nextbike-live.json"

    def __init__(self, city_id: str):
        self.city_id = city_id

    def fetch_data(self) -> dict:
        """
        Fetch Nextbike data for a specific city by it's city ID.
        Using Nextbike GPFS API v2
        """
        params = {"city": self.city_id}
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def extract_places(data: dict) -> list[dict]:
        """
        Places in Nextbike can be stations AND bikes.
        Some bikes might not be returned to stations.
        Some bikes pile up at one location and make a new 'place'.
        """
        try:
            # Access countries[0]["cities"][0]["places"] safely
            places = (
                data.get("countries", [{}])[0].get("cities", [{}])[0].get("places", [])
            )
        except (IndexError, KeyError):
            places = []
        return places

    @staticmethod
    def get_city_info(data: dict) -> dict:
        try:
            city = data.get("countries", [{}])[0]
            city_info = {
                "city_id": city.get("cities", [{}])[0].get("uid", 0),
                "city_name": city.get("cities", [{}])[0].get("name", "Unknown"),
                "timezone": city.get("timezone", "Unknown"),
                "latitude": city.get("lat", 0),
                "longitude": city.get("lng", 0),
                "set_point_bikes": city.get("set_point_bikes", 0),
                "available_bikes": city.get("available_bikes", 0),
                "last_updated": datetime.datetime.now(),
            }
        except (IndexError, KeyError):
            city_info = {}

        return city_info


def write_city_info_to_database(city_info):
    conn_str: str = (
        f"host={db_host} dbname={db_name} user={db_user} password={db_password}"
    )
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            city_sql = """
            INSERT INTO public.cities (
                city_id, city_name, timezone, latitude, longitude, set_point_bikes, available_bikes, last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """
            cur.execute(city_sql, tuple(city_info.values()))

        conn.commit()

    return


def write_to_database(bike_entries, station_entries):
    conn_str: str = (
        f"host={db_host} dbname={db_name} user={db_user} password={db_password}"
    )
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            bike_sql = """
            INSERT INTO public.bikes (
                bike_number, latitude, longitude, active, state, bike_type, station_number, station_uid, last_updated, city_id, city_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """
            cur.executemany(bike_sql, bike_entries)

            station_sql = """
            INSERT INTO public.stations (
                uid, latitude, longitude, name, spot, station_number, maintenance, terminal_type, last_updated, city_id, city_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """
            cur.executemany(station_sql, station_entries)

        conn.commit()

    return


def build_bike_entries(
    places: list[dict], city_id: str, city_name: str, timestamp: datetime.datetime
) -> list[tuple]:
    bike_entries = []
    for place in places:
        for bike in place.get("bike_list", []):
            bike_entries.append(
                (
                    bike.get("number", ""),
                    place.get("lat", 0),
                    place.get("lng", 0),
                    bike.get("active", None),
                    bike.get("state", ""),
                    bike.get("bike_type", ""),
                    place.get("number", 0),
                    place.get("uid", 0),
                    timestamp,
                    city_id,
                    city_name,
                )
            )
    return bike_entries


def build_station_entries(
    places: list[dict], city_id: str, city_name: str, timestamp: datetime.datetime
) -> list[tuple]:
    station_entries = []
    for place in places:
        if place.get("bike") is False:
            station_entries.append(
                (
                    place.get("uid", 0),
                    place.get("lat", 0),
                    place.get("lng", 0),
                    place.get("name", "Unknown"),
                    place.get("spot", None),
                    place.get("number", 0),
                    place.get("maintenance", None),
                    place.get("terminal_type", "Unknown"),
                    timestamp,
                    city_id,
                    city_name,
                )
            )

    return station_entries


# ---------- Console output ----------
class ConsolePrinter:
    """Print nextbike info to console"""

    @staticmethod
    def print_summary(city_info: dict, bike_entries: list, station_entries: list):
        print("City info:", city_info)
        print(
            f"Bike entries: {len(bike_entries)}, Station entries: {len(station_entries)}"
        )
        print("-" * 40)


# ---------- CLI parser ----------
class NextbikeCLI:
    def __init__(self, env_city_ids=None):
        self.env_city_ids = env_city_ids or []
        self.city_ids = []

    def parse_args(self, args=None):
        parser = argparse.ArgumentParser(description="Nextbike data collector CLI")
        parser.add_argument(
            "--city-ids",
            type=int,
            nargs="+",
            default=None,
            help="City ID(s) to fetch. Defaults to .env CITY_IDS.",
        )
        parser.add_argument(
            "--save", action="store_true", help="Save fetched Nextbike data to database"
        )
        parsed = parser.parse_args(args)

        self.city_ids = parsed.city_ids

        return parsed


class AppConfig:
    def __init__(self, cli_city_ids=[]):
        self.city_ids = []
        environment_city_ids = []

        load_dotenv()
        env_city_ids = os.getenv("CITY_IDS", None)

        if cli_city_ids:
            self.city_ids = cli_city_ids
        elif env_city_ids:
            for city_id in env_city_ids.split(","):
                environment_city_ids.append(int(city_id))
            self.city_ids = environment_city_ids
        else:
            raise ValueError(
                "No city ID provided. Use --city-ids or set CITY_IDS in .env."
            )
        return


def main():
    cli = NextbikeCLI()
    config = AppConfig(cli.city_ids)

    last_updated = datetime.datetime.now()

    city_ids = cli.city_ids
    for city_id in city_ids:
        print(f"Collecting nextbike data from city: {city_id}")
        api = NextbikeAPI(city_id)
        data = api.fetch_data()
        city_info = api.get_city_info(data)
        places = api.extract_places(data)

        city_name = (
            data.get("countries", [{}])[0].get("cities", [{}])[0].get("name", "Unknown")
        )

        bike_entries = build_bike_entries(places, city_id, city_name, last_updated)
        station_entries = build_station_entries(
            places, city_id, city_name, last_updated
        )

        ConsolePrinter.print_summary(city_info, bike_entries, station_entries)

        if args.save:
            write_to_database(bike_entries, station_entries)
            write_city_info_to_database(city_info)
            print(f"Data saed for city {city_info['city_name']}.")


if __name__ == "__main__":
    main()
