import os

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI()


def get_connection():
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


@app.get("/api/available")
def available():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.city_id,
                       COALESCE(c.city_name, t.city_id::text) AS city_name,
                       array_agg(DISTINCT DATE(t.start_time)::text ORDER BY DATE(t.start_time)::text DESC)
                FROM public.trips t
                LEFT JOIN public.cities c ON t.city_id = c.city_id
                GROUP BY t.city_id, c.city_name
                ORDER BY t.city_id
            """)
            rows = cur.fetchall()
    return [{"city_id": str(row[0]), "city_name": row[1], "dates": row[2]} for row in rows]


@app.get("/api/trips")
def trips(city_id: int, date: str):
    if not date:
        raise HTTPException(status_code=400, detail="date parameter is required")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.bike_number,
                       t.start_time::text,
                       t.end_time::text,
                       t.duration_seconds,
                       r.distance_meters,
                       r.coordinates,
                       t.route_id
                FROM public.trips t
                LEFT JOIN public.routes r ON t.route_id = r.id
                WHERE t.city_id = %s AND DATE(t.start_time) = %s
                ORDER BY t.start_time
            """, (city_id, date))
            rows = cur.fetchall()

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": row[5] or []},
            "properties": {
                "bike_number": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "duration": row[3],
                "distance": row[4] or 0,
                "route_id": row[6],
            },
        }
        for row in rows
    ]
    return {"type": "FeatureCollection", "features": features}


@app.get("/api/stations")
def stations(city_id: int, date: str):
    if not date:
        raise HTTPException(status_code=400, detail="date parameter is required")
    with get_connection() as conn:
        with conn.cursor() as cur:
            # First, find the latest available date for this city (on or before the requested date)
            cur.execute("""
                SELECT MAX(DATE(last_updated))
                FROM public.stations
                WHERE city_id = %s AND DATE(last_updated) <= %s::date
            """, (city_id, date))
            result = cur.fetchone()
            latest_date = result[0] if result[0] else date
            
            cur.execute("""
                WITH station_data AS (
                    SELECT id, uid, latitude, longitude, name, spot, station_number,
                           maintenance, terminal_type, city_id, city_name,
                           ROW_NUMBER() OVER (
                               PARTITION BY uid, latitude, longitude, name, spot,
                                            station_number, terminal_type, DATE(last_updated), maintenance
                               ORDER BY last_updated DESC
                           ) AS rn
                    FROM public.stations
                    WHERE city_id = %s AND DATE(last_updated) = %s
                ),
                filtered_stations AS (
                    SELECT id, uid, latitude, longitude, name, spot, station_number,
                           maintenance, terminal_type, city_id, city_name
                    FROM station_data WHERE rn = 1
                ),
                bike_data AS (
                    SELECT DATE_TRUNC('minute', last_updated) AS minute,
                           station_number,
                           COUNT(bike_number) AS bike_count,
                           STRING_AGG(bike_number::TEXT, ', ') AS bike_list
                    FROM public.bikes
                    WHERE city_id = %s AND DATE(last_updated) = %s
                    GROUP BY DATE_TRUNC('minute', last_updated), station_number
                ),
                distinct_minutes AS (
                    SELECT DISTINCT DATE_TRUNC('minute', last_updated) AS minute
                    FROM public.bikes
                    WHERE city_id = %s AND DATE(last_updated) = %s
                ),
                station_minute_combinations AS (
                    SELECT dm.minute, fs.*
                    FROM distinct_minutes dm CROSS JOIN filtered_stations fs
                ),
                station_bike_combined AS (
                    SELECT smc.minute, smc.id, smc.uid, smc.latitude, smc.longitude,
                           smc.name, smc.spot, smc.station_number, smc.maintenance,
                           smc.terminal_type, smc.city_id, smc.city_name,
                           COALESCE(bd.bike_count, 0) AS bike_count,
                           COALESCE(bd.bike_list, '') AS bike_list
                    FROM station_minute_combinations smc
                    LEFT JOIN bike_data bd
                        ON smc.station_number = bd.station_number AND smc.minute = bd.minute
                ),
                bike_changes AS (
                    SELECT *,
                           LAG(bike_count) OVER (PARTITION BY station_number ORDER BY minute) AS previous_bike_count
                    FROM station_bike_combined
                )
                SELECT minute, id, uid, latitude, longitude, name, spot, station_number,
                       maintenance, terminal_type, city_id, city_name, bike_count, bike_list
                FROM bike_changes
                WHERE bike_count IS DISTINCT FROM previous_bike_count
                ORDER BY station_number, minute
            """, (city_id, latest_date, city_id, latest_date, city_id, latest_date))
            rows = cur.fetchall()

    return [
        {
            "minute": row[0].strftime("%Y-%m-%dT%H:%M:%S"),
            "id": row[1],
            "uid": row[2],
            "latitude": row[3],
            "longitude": row[4],
            "name": row[5],
            "spot": row[6],
            "station_number": row[7],
            "maintenance": row[8],
            "terminal_type": row[9],
            "city_id": row[10],
            "city_name": row[11],
            "bike_count": row[12],
            "bike_list": row[13] or "",
        }
        for row in rows
    ]


# Serve data files (geojson.gz, csv.gz, manifest) - also used for station files
app.mount("/data", StaticFiles(directory="/app/data"), name="data")

# Serve visualization static files - must be last (catch-all)
app.mount("/", StaticFiles(directory="/app", html=True), name="static")
