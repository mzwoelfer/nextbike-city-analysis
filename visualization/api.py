import os
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI()


def to_city_iso(timestamp, city_timezone):
    city_zone = ZoneInfo(city_timezone)
    return timestamp.astimezone(city_zone).isoformat(timespec="seconds")


def get_connection():
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        row_factory=dict_row,
    )


@app.get("/api/available")
def available():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.city_id,
                       COALESCE(c.city_name, t.city_id::text) AS city_name,
                       array_agg(DISTINCT DATE(t.start_time AT TIME ZONE COALESCE(c.timezone, 'UTC'))::text
                                 ORDER BY DATE(t.start_time AT TIME ZONE COALESCE(c.timezone, 'UTC'))::text DESC) AS dates
                FROM public.trips t
                LEFT JOIN public.cities c ON t.city_id = c.city_id
                GROUP BY t.city_id, c.city_name
                ORDER BY t.city_id
            """)
            rows = cur.fetchall()
    return [
        {"city_id": str(row["city_id"]), "city_name": row["city_name"], "dates": row["dates"]}
        for row in rows
    ]


@app.get("/api/trips")
def trips(city_id: int, date: str):
    if not date:
        raise HTTPException(status_code=400, detail="date parameter is required")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.bike_number,
                       t.start_time,
                       t.end_time,
                       t.duration_seconds,
                       r.distance_meters AS distance_meters,
                       r.coordinates,
                       t.route_id,
                       COALESCE(c.timezone, 'UTC') AS city_timezone
                FROM public.trips t
                LEFT JOIN public.routes r ON t.route_id = r.id
                LEFT JOIN public.cities c ON t.city_id = c.city_id
                WHERE t.city_id = %s AND DATE(t.start_time AT TIME ZONE COALESCE(c.timezone, 'UTC')) = %s
                ORDER BY t.start_time
            """, (city_id, date))
            rows = cur.fetchall()

    city_timezone = rows[0]["city_timezone"] if rows else "UTC"

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": row["coordinates"] or []},
            "properties": {
                "bike_number": row["bike_number"],
                "start_time": to_city_iso(row["start_time"], row["city_timezone"]),
                "end_time": to_city_iso(row["end_time"], row["city_timezone"]),
                "duration": row["duration_seconds"],
                "distance": row["distance_meters"] or 0,
                "route_id": row["route_id"],
                "timezone": row["city_timezone"],
            },
        }
        for row in rows
    ]
    return {
        "type": "FeatureCollection",
        "timezone": city_timezone,
        "features": features,
    }


@app.get("/api/bikes")
def bikes(city_id: int, date: str):
    if not date:
        raise HTTPException(status_code=400, detail="date parameter is required")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                WITH city_context AS (
                    SELECT COALESCE(timezone, 'UTC') AS city_timezone
                    FROM public.cities
                    WHERE city_id = %s
                ),
                standalone_bike_ids AS (
                    SELECT DISTINCT b.bike_number
                    FROM public.bikes b
                    JOIN city_context cc ON TRUE
                    WHERE b.city_id = %s
                      AND DATE(b.last_updated AT TIME ZONE cc.city_timezone) = %s
                      AND COALESCE(b.station_number, 0) = 0
                ),
                bike_observations AS (
                    SELECT b.bike_number,
                           b.latitude,
                           b.longitude,
                           b.station_number,
                           COALESCE(b.bike_type, '') AS bike_type,
                           DATE_TRUNC('minute', b.last_updated AT TIME ZONE cc.city_timezone) AS minute,
                           b.last_updated,
                           cc.city_timezone
                    FROM public.bikes b
                    JOIN city_context cc ON TRUE
                    WHERE b.city_id = %s
                      AND DATE(b.last_updated AT TIME ZONE cc.city_timezone) = %s
                      AND b.bike_number IN (SELECT bike_number FROM standalone_bike_ids)
                )
                SELECT DISTINCT ON (minute, bike_number)
                       bike_number, latitude, longitude, station_number,
                       bike_type, minute, city_timezone
                FROM bike_observations
                ORDER BY minute, bike_number, last_updated DESC
            """, (city_id, city_id, date, city_id, date))
            rows = cur.fetchall()

    city_timezone = rows[0]["city_timezone"] if rows else "UTC"
    return {
        "timezone": city_timezone,
        "bikes": [
            {
                "bike_number": row["bike_number"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "station_number": row["station_number"],
                "bike_type": row["bike_type"],
                "minute": row["minute"].replace(tzinfo=ZoneInfo(row["city_timezone"])).isoformat(timespec="seconds"),
                "timezone": row["city_timezone"],
            }
            for row in rows
        ],
    }


@app.get("/api/stations")
def stations(city_id: int, date: str):
    if not date:
        raise HTTPException(status_code=400, detail="date parameter is required")
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Fetch city timezone once; use it for all subsequent date filters
            cur.execute(
                "SELECT COALESCE(timezone, 'UTC') AS city_timezone FROM public.cities WHERE city_id = %s",
                (city_id,)
            )
            tz_row = cur.fetchone()
            city_tz = tz_row["city_timezone"] if tz_row else 'UTC'

            # First, find the latest available date for this city (on or before the requested date)
            cur.execute("""
                SELECT MAX(DATE(last_updated AT TIME ZONE %s)) AS latest_date
                FROM public.stations
                WHERE city_id = %s AND DATE(last_updated AT TIME ZONE %s) <= %s::date
            """, (city_tz, city_id, city_tz, date))
            result = cur.fetchone()
            latest_date = result["latest_date"] if result["latest_date"] else date
            
            cur.execute("""
                WITH station_data AS (
                    SELECT id, uid, latitude, longitude, name, spot, station_number,
                           maintenance, terminal_type, city_id, city_name,
                           ROW_NUMBER() OVER (
                               PARTITION BY uid, latitude, longitude, name, spot,
                                            station_number, terminal_type, DATE(last_updated AT TIME ZONE %s), maintenance
                               ORDER BY last_updated DESC
                           ) AS rn
                    FROM public.stations
                    WHERE city_id = %s AND DATE(last_updated AT TIME ZONE %s) = %s
                ),
                filtered_stations AS (
                    SELECT id, uid, latitude, longitude, name, spot, station_number,
                           maintenance, terminal_type, city_id, city_name
                    FROM station_data WHERE rn = 1
                ),
                bike_source AS (
                    SELECT (last_updated AT TIME ZONE %s) AS local_ts,
                           station_number,
                           bike_number,
                           COALESCE(NULLIF(bike_type, ''), 'unknown') AS bike_type
                    FROM public.bikes
                    WHERE city_id = %s AND DATE(last_updated AT TIME ZONE %s) = %s
                ),
                bike_type_data AS (
                    SELECT minute, station_number,
                           jsonb_object_agg(bike_type, type_count) AS bike_type_counts
                    FROM (
                        SELECT DATE_TRUNC('minute', local_ts) AS minute,
                               station_number,
                               bike_type,
                               COUNT(*) AS type_count
                        FROM bike_source
                        GROUP BY DATE_TRUNC('minute', local_ts), station_number, bike_type
                    ) type_counts
                    GROUP BY minute, station_number
                ),
                bike_data AS (
                    SELECT DATE_TRUNC('minute', local_ts) AS minute,
                           station_number,
                           COUNT(bike_number) AS bike_count,
                           STRING_AGG(bike_number::TEXT, ', ') AS bike_list
                    FROM bike_source
                    GROUP BY DATE_TRUNC('minute', local_ts), station_number
                ),
                distinct_minutes AS (
                    SELECT DISTINCT DATE_TRUNC('minute', local_ts) AS minute
                    FROM bike_source
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
                              COALESCE(bd.bike_list, '') AS bike_list,
                              COALESCE(btd.bike_type_counts, '{}'::jsonb) AS bike_type_counts
                    FROM station_minute_combinations smc
                    LEFT JOIN bike_data bd
                        ON smc.station_number = bd.station_number AND smc.minute = bd.minute
                          LEFT JOIN bike_type_data btd
                           ON smc.station_number = btd.station_number AND smc.minute = btd.minute
                ),
                bike_changes AS (
                    SELECT *,
                              LAG(bike_count) OVER (PARTITION BY station_number ORDER BY minute) AS previous_bike_count,
                              LAG(bike_type_counts) OVER (PARTITION BY station_number ORDER BY minute) AS previous_bike_type_counts
                    FROM station_bike_combined
                )
                SELECT minute, id, uid, latitude, longitude, name, spot, station_number,
                          maintenance, terminal_type, city_id, city_name, bike_count, bike_list,
                          bike_type_counts
                FROM bike_changes
                      WHERE bike_count IS DISTINCT FROM previous_bike_count
                         OR bike_type_counts IS DISTINCT FROM previous_bike_type_counts
                ORDER BY station_number, minute
            """, (
                city_tz, city_id, city_tz, latest_date,   # station_data
                city_tz, city_id, city_tz, latest_date,   # bike_source
            ))
            rows = cur.fetchall()

    return [
        {
            "minute": row["minute"].replace(tzinfo=ZoneInfo(city_tz)).isoformat(timespec="seconds"),
            "id": row["id"],
            "uid": row["uid"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "name": row["name"],
            "spot": row["spot"],
            "station_number": row["station_number"],
            "maintenance": row["maintenance"],
            "terminal_type": row["terminal_type"],
            "city_id": row["city_id"],
            "city_name": row["city_name"],
            "bike_count": row["bike_count"],
            "bike_list": row["bike_list"] or "",
            "bike_type_counts": row["bike_type_counts"] or {},
            "timezone": city_tz,
        }
        for row in rows
    ]


# Serve data files (geojson.gz, csv.gz, manifest) - also used for station files
app_directory = Path(__file__).resolve().parent
app.mount("/data", StaticFiles(directory=app_directory / "data"), name="data")

# Serve visualization static files - must be last (catch-all)
app.mount("/", StaticFiles(directory=app_directory, html=True), name="static")
