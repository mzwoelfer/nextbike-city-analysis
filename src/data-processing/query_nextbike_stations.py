import requests
import datetime
import psycopg
import config
import traceback

if __name__ == "__main__":
    query_date = datetime.datetime.now()

    URL = (
        "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_ng/en/station_information.json"
    )

    response = requests.get(url=URL)
    try:
        r = response.json()

        conn_str = f"host={config.dbhost} dbname={config.dbname} user={config.dbuser} password={config.dbpassword}"

        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                for station in r["data"]["stations"]:
                    station_id = station["station_id"]
                    name = station["name"]
                    lat = station["lat"]
                    lon = station["lon"]

                    cur.execute(
                        """
                        INSERT INTO public.stations ("station_id", "latitude", "longitude", "firstListed", "lastListed", "name")
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT ("station_id") DO UPDATE SET "lastListed" = EXCLUDED."lastListed";
                        """,
                        (
                            station_id,
                            lat,
                            lon,
                            query_date,
                            query_date,
                            name,
                        ),
                    )
            conn.commit()

    except Exception:
        traceback.print_exc()
