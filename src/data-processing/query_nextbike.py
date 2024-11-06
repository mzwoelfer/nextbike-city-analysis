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


def insert_bike_data(cur, bike, timestamp):
    sql = """
    INSERT INTO public.bikes (bike_number, bike_type, latitude, longitude, timestamp, active, state, last_updated)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (bike_number, timestamp) DO NOTHING;
    """
    cur.execute(
        sql,
        (
            bike["number"],
            bike["bike_type"],
            bike["lat"],
            bike["lng"],
            timestamp,
            bike["active"],
            bike["state"],
            bike["last_updated"],
        ),
    )


def insert_station_data(cur, station, timestamp):
    sql = """
    INSERT INTO public.stations (uid, latitude, longitude, timestamp, name, spot, station_number, maintenance, terminal_type, last_updated)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (uid, timestamp) DO NOTHING;
    """
    cur.execute(
        sql,
        (
            station["uid"],
            station["lat"],
            station["lng"],
            timestamp,
            station["name"],
            station["spot"],
            station["number"],
            station["maintenance"],
            station["terminal_type"],
            station["last_updated"],
        ),
    )


def main():
    conn_str = f"host={config.dbhost} dbname={config.dbname} user={config.dbuser} password={config.dbpassword}"

    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            data = fetch_data()
            timestamp = datetime.datetime.now()

            for country in data.get("countries", []):
                for city in country.get("cities", []):
                    for place in city.get("places", []):
                        for bike in place.get("bike_list", []):
                            insert_bike_data(cur, bike, timestamp)

                        insert_station_data(cur, place, timestamp)


if __name__ == "__main__":
    main()
