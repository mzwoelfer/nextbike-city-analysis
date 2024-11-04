import requests
import datetime
import os
import psycopg
import config
import logging


def get_nextbike_locations():
    # request data
    URL = "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_ng/en/free_bike_status.json"

    # sending get request and saving the response as response object
    response = requests.get(url=URL)
    try:
        r = response.json()
        nextbikes = []
        # Connect to an existing database
        query_date = datetime.datetime.now()
        NEXTBIKE = 0
        for bike in r["data"]["bikes"]:
            try:
                bike_id = int(bike["bike_id"])
            except:
                # single bike have no ID (?!); skip these bikes
                continue

            lat = bike["lat"]
            lon = bike["lon"]
            nextbikes.append([bike_id, NEXTBIKE, query_date, lat, lon])
        return nextbikes
    except Exception as e:
        logging.exception("Error fetching nextbike data", exc_info=True)
        return []


if __name__ == "__main__":

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    logging.basicConfig(level=logging.INFO, filename="logfile.log")
    logger = logging.getLogger(__name__)

    nextbikes = get_nextbike_locations()

    # Connection string for psycopg (new version)
    conn_str = f"host={config.dbhost} dbname={config.dbname} user={config.dbuser} password={config.dbpassword}"

    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO public."bikeLocations" (id, "bikeId", "providerId", "timestamp", latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """
            # Executing batch insertion using execute_batch for psycopg
            psycopg.sql.SQL(cur.execute(sql, (DEFAULT, *bike)) for bike in nextbikes)

        conn.commit()
