import requests
import datetime
import psycopg
import config
import traceback

if __name__ == "__main__":
    query_date = datetime.datetime.now()

    # request data
    URL = (
        "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_ng/en/station_information.json"
    )

    # sending get request and saving the response as response object
    response = requests.get(url=URL)
    try:
        r = response.json()

        # Connection string for psycopg (new version)
        conn_str = f"host={config.dbhost} dbname={config.dbname} user={config.dbuser} password={config.dbpassword}"

        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                for station in r["data"]["stations"]:
                    station_id = int(station["station_id"])
                    name = station["name"]
                    short_name = station["short_name"]
                    capacity = station.get("capacity")  # using .get() for safe access
                    lat = station["lat"]
                    lon = station["lon"]

                    # Insert into db - update "lastListed" of existing stations with every new query and add new stations
                    cur.execute(
                        """
                        INSERT INTO public.stations ("id", "latitude", "longitude", "firstListed", "lastListed", "name", "short_name", "capacity")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT ("id") DO UPDATE SET "lastListed" = EXCLUDED."lastListed";
                        """,
                        (
                            station_id,
                            lat,
                            lon,
                            query_date,
                            query_date,
                            name,
                            short_name,
                            capacity,
                        ),
                    )
            conn.commit()

    except Exception:
        traceback.print_exc()
