from database.base import DatabaseClient
from dataclasses import dataclass
import requests
import argparse
import datetime
import os
from dotenv import load_dotenv

# ---------- DATA CLASSES ----------
@dataclass
class City:
    city_id: int
    city_name: str
    timezone: str
    latitude: float
    longitude: float
    set_point_bikes: int
    available_bikes: int
    last_updated: datetime.datetime

    @classmethod
    def from_api_data(cls, data: dict):
        country = data.get("countries", [{}])[0]
        city_data = country.get("cities", [{}])[0]
        return cls(
            city_id=city_data.get("uid", 0),
            city_name=city_data.get("name", "Unknown"),
            timezone=country.get("timezone", "Unknown"),
            latitude=country.get("lat", 0),
            longitude=country.get("lng", 0),
            set_point_bikes=country.get("set_point_bikes", 0),
            available_bikes=country.get("available_bikes", 0),
            last_updated=datetime.datetime.now(),
        )

    def as_tuple(self) -> tuple:
        return (
            self.city_id,
            self.city_name,
            self.timezone,
            self.latitude,
            self.longitude,
            self.set_point_bikes,
            self.available_bikes,
            self.last_updated,
        )


@dataclass
class Bike:
    bike_number: str
    latitude: float
    longitude: float
    active: bool
    state: str
    bike_type: str
    station_number: int
    station_uid: int
    last_updated: datetime.datetime
    city_id: int
    city_name: str

    def as_tuple(self) -> tuple:
        """Convert this Bike to a tuple"""
        return (
            self.bike_number,
            self.latitude,
            self.longitude,
            self.active,
            self.state,
            self.bike_type,
            self.station_number,
            self.station_uid,
            self.last_updated,
            self.city_id,
            self.city_name,
        )

    @classmethod
    def bike_entries_from_place(
        cls,
        places: list[dict],
        city_id: int,
        city_name: str,
        timestamp: datetime.datetime,
    ):
        bikes = []
        for place in places:
            for bike in place.get("bike_list", []):
                bikes.append(
                    cls(
                        bike_number=bike.get("number", ""),
                        latitude=place.get("lat", 0),
                        longitude=place.get("lat", 0),
                        active=bike.get("active", None),
                        state=bike.get("state", ""),
                        bike_type=bike.get("bike_type", ""),
                        station_number=place.get("number", 0),
                        station_uid=place.get("uid", 0),
                        last_updated=timestamp,
                        city_id=city_id,
                        city_name=city_name,
                    )
                )
        return bikes


@dataclass
class Station:
    uid: int
    latitude: float
    longitude: float
    name: str
    spot: bool
    station_number: int
    maintenance: bool
    terminal_type: str
    last_updated: datetime.datetime
    city_id: int
    city_name: str

    def as_tuple(self) -> tuple:
        """Convert this Station to a tuple"""
        return (
            self.uid,
            self.latitude,
            self.longitude,
            self.name,
            self.spot,
            self.station_number,
            self.maintenance,
            self.terminal_type,
            self.last_updated,
            self.city_id,
            self.city_name,
        )

    @classmethod
    def build_station_entries(
        cls,
        places: list[dict],
        city_id: int,
        city_name: str,
        timestamp: datetime.datetime,
    ) -> list[tuple]:
        station_entries = []
        for place in places:
            if place.get("bike") is False:
                station_entries.append(
                    cls(
                        uid=place.get("uid", 0),
                        latitude=place.get("lat", 0),
                        longitude=place.get("lng", 0),
                        name=place.get("name", "Unknown"),
                        spot=place.get("spot", None),
                        station_number=place.get("number", 0),
                        maintenance=place.get("maintenance", None),
                        terminal_type=place.get("terminal_type", "Unknown"),
                        last_updated=timestamp,
                        city_id=city_id,
                        city_name=city_name,
                    )
                )

        return station_entries


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


# ---------- Console output ----------
class ConsolePrinter:
    """Print nextbike info to console"""

    @staticmethod
    def print_summary(city: City, bike_entries: list, station_entries: list):
        print("City info:", city)
        print(
            f"Bike entries: {len(bike_entries)}, Station entries: {len(station_entries)}"
        )
        print("-" * 40)


# ---------- CLI parser ----------
class NextbikeCLI:
    def __init__(self, args=None):
        parsed = self._parse_args(args=args)
        self.city_ids = parsed.city_ids
        self.save = parsed.save

    def _parse_args(self, args=None):
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

        return parsed


class AppConfig:
    def __init__(self, cli_city_ids=[]):
        self.city_ids = []
        environment_city_ids = []

        load_dotenv()
        self.db_type = os.getenv("DB_TYPE", "postgres").lower()
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")

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

def main():
    cli = NextbikeCLI()
    config = AppConfig(cli.city_ids)
    last_updated = datetime.datetime.now()

    db = DatabaseClient(config)

    city_ids = config.city_ids
    for city_id in city_ids:
        print(f"Collecting nextbike data from city: {city_id}")
        api = NextbikeAPI(city_id)
        data = api.fetch_data()
        city = City.from_api_data(data)
        places = api.extract_places(data)

        bike_entries = Bike.bike_entries_from_place(
            places, city.city_id, city.city_name, last_updated
        )
        station_entries = Station.build_station_entries(
            places, city.city_id, city.city_name, last_updated
        )

        ConsolePrinter.print_summary(city, bike_entries, station_entries)

        if cli.save:
            db.insert_city_information(city)
            db.insert_bike_entries(bike_entries)
            db.insert_station_entries(station_entries)
            print(f"Data saed for city {city.city_name}.")


if __name__ == "__main__":
    main()
