import requests
import datetime
import os
import psycopg
import config
import logging


def get_nextbike_locations():
    URL = "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_ng/en/free_bike_status.json"

    response = requests.get(url=URL)
    try:
        r = response.json()
        nextbikes = []
        query_date = datetime.datetime.now()

        version = r.get("version", "Unknown")
        last_updated = r.get("last_updated", 0)
        ttl = r.get("ttl", 0)

        # Iterate over each bike
        for bike in r["data"]["bikes"]:
            try:
                bike_id = bike["bike_id"]
            except KeyError:
                logging.warning("Bike ID missing; skipping this bike entry")
                continue

            lat = bike.get("lat")
            lon = bike.get("lon")
            station_id = bike.get("station_id", "Unknown")
            vehicle_type_id = bike.get("vehicle_type_id")
            is_reserved = bike.get("is_reserved", False)
            is_disabled = bike.get("is_disabled", False)

            nextbikes.append(
                (
                    bike_id,
                    query_date,
                    station_id,
                    vehicle_type_id,
                    lat,
                    lon,
                    is_reserved,
                    is_disabled,
                    version,
                    last_updated,
                    ttl,
                )
            )

        logging.info("Fetched nextbike locations")
        return nextbikes
    except Exception as e:
        logging.exception("Error fetching nextbike data", exc_info=True)
        return []


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    logging.basicConfig(level=logging.INFO, filename="logfile.log")
    logger = logging.getLogger(__name__)

    nextbikes = get_nextbike_locations()
    conn_str = f"host={config.dbhost} dbname={config.dbname} user={config.dbuser} password={config.dbpassword}"

    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO public."bikeLocations" (
                "bikeId", "timestamp", "stationId", "vehicleTypeId",
                latitude, longitude, "is_reserved", "is_disabled",
                "version", "last_updated", "ttl"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """
            cur.executemany(sql, nextbikes)

        conn.commit()
