import requests
import datetime
import psycopg
import config


def fetch_data():
    url = "https://maps.nextbike.net/maps/nextbike-live.json"
    params = {
        "city": "467",  # Gießen city ID
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_bike_entries(bike_list, timestamp):
    bike_entries = []
    for bike in bike_list:
        bike_entries.append(
            (
                bike.get("number"),
                bike.get("bike_type"),
                bike.get("lat"),
                bike.get("lng"),
                timestamp,
                bike.get("active"),
                bike.get("state"),
                bike.get("last_updated"),
            )
        )
    return bike_entries


def get_station_entries(places, timestamp):
    station_entries = []
    for place in places:
        station_entries.append(
            (
                place.get("uid"),
                place.get("lat"),
                place.get("lng"),
                timestamp,
                place.get("name"),
                place.get("spot"),
                place.get("number"),
                place.get("maintenance"),
                place.get("terminal_type"),
                place.get("last_updated"),
            )
        )
    return station_entries


def get_places(data):
    try:
        # Access countries[0]["cities"][0]["places"] safely
        places = data.get("countries", [{}])[0].get("cities", [{}])[0].get("places", [])
    except (IndexError, KeyError):
        places = []
    return places


def write_to_database(bike_entries, station_entries):
    conn_str: str = (
        f"host={config.dbhost} dbname={config.dbname} user={config.dbuser} password={config.dbpassword}"
    )
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            bike_sql = """
            INSERT INTO public.bikes (
                bike_number, latitude, longitude, active, state, bike_type, timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (bike_number, timestamp) DO NOTHING;
            """
            cur.executemany(bike_sql, bike_entries)

            station_sql = """
            INSERT INTO public.stations (
                uid, latitude, longitude, name, spot, station_number, maintenance, terminal_type, timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (uid, timestamp) DO NOTHING;
            """
            cur.executemany(station_sql, station_entries)

        conn.commit()

    return


def main():

    data = fetch_data()
    timestamp = datetime.datetime.now()

    bike_entries = []
    station_entries = []
    places = get_places(data)

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
                    timestamp,
                    bike.get("number", ""),
                    place_lat,
                    place_lng,
                    bike.get("active", None),
                    bike.get("state", ""),
                    bike.get("bike_type", ""),
                    timestamp,
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
                    timestamp,
                )
            )
    print(station_entries, bike_entries)

    # write_to_database(bike_entries, station_entries)


if __name__ == "__main__":
    main()
