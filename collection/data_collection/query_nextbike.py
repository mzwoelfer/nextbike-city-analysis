import requests
import datetime
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
city_id = os.getenv("CITY_ID")


def fetch_data(city_id):
    """
    Fetch Nextbike data for a specific city by it's city ID.
    Using Nextbike GPFS API v2
    """
    url = "https://maps.nextbike.net/maps/nextbike-live.json"
    params = {"city": city_id}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_places(data):
    try:
        # Access countries[0]["cities"][0]["places"] safely
        places = data.get("countries", [{}])[0].get("cities", [{}])[0].get("places", [])
    except (IndexError, KeyError):
        places = []
    return places


def get_city_info(data):
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


def main():
    last_updated = datetime.datetime.now()

    city_ids = [467, 438]

    for city_id in city_ids:
        print(f"Collecting nextbike data from city: {city_id}")

        data = fetch_data(city_id)

        city_name = (
            data.get("countries", [{}])[0].get("cities", [{}])[0].get("name", "Unknown")
        )
        places = get_places(data)

        bike_entries = []
        station_entries = []

        for place in places:
            place_uid = place.get("uid", 0)
            place_lat = place.get("lat", 0)
            place_lng = place.get("lng", 0)
            place_is_bike = place.get("bike", None)
            place_name = place.get("name", "Unknown")
            place_spot = place.get("spot", None)
            place_number = place.get("number", 0)
            place_maintenance = place.get("maintenance", None)
            place_terminal_type = place.get("terminal_type", "Unknown")

            for bike in place.get("bike_list", []):
                bike_entries.append(
                    (
                        bike.get("number", ""),
                        place_lat,
                        place_lng,
                        bike.get("active", None),
                        bike.get("state", ""),
                        bike.get("bike_type", ""),
                        place_number,
                        place_uid,
                        last_updated,
                        city_id,
                        city_name,
                    )
                )

            if place_is_bike is False:
                station_entries.append(
                    (
                        place_uid,
                        place_lat,
                        place_lng,
                        place_name,
                        place_spot,
                        place_number,
                        place_maintenance,
                        place_terminal_type,
                        last_updated,
                        city_id,
                        city_name,
                    )
                )
        city_info = get_city_info(data)
        write_to_database(bike_entries, station_entries)
        write_city_info_to_database(city_info)


if __name__ == "__main__":
    main()
