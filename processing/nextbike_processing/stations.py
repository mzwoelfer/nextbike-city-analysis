import os
import pandas as pd
from zoneinfo import ZoneInfo
from nextbike_processing.database import get_connection
from nextbike_processing.utils import save_csv, save_gzipped_csv, save_json


def fetch_station_data(city_id, date):
    query = """
    WITH city_context AS (
            SELECT city_id, COALESCE(timezone, 'UTC') AS city_tz
            FROM public.cities
            WHERE city_id = %s
        ),
        station_data AS (
            SELECT
                id,
                uid,
                latitude,
                longitude,
                name,
                spot,
                station_number,
                maintenance,
                terminal_type,
                city_id,
                city_name,
                ROW_NUMBER() OVER (
                    PARTITION BY uid, latitude, longitude, name, spot, station_number, terminal_type,
                                 DATE(last_updated AT TIME ZONE cc.city_tz), maintenance
                    ORDER BY last_updated DESC
                ) AS rn
            FROM public.stations
            JOIN city_context cc ON cc.city_id = public.stations.city_id
            WHERE public.stations.city_id = %s
            AND DATE(last_updated AT TIME ZONE cc.city_tz) = %s
        ),
        filtered_stations AS (
            SELECT
                id,
                uid,
                latitude,
                longitude,
                name,
                spot,
                station_number,
                maintenance,
                terminal_type,
                city_id,
                city_name
            FROM station_data
            WHERE rn = 1
        ),
        bike_data AS (
            SELECT
                DATE_TRUNC('minute', b.last_updated AT TIME ZONE cc.city_tz) AS minute,
                b.station_number,
                COUNT(b.bike_number) AS bike_count,
                STRING_AGG(b.bike_number::TEXT, ', ') AS bike_list
            FROM
                public.bikes b
            JOIN city_context cc ON cc.city_id = b.city_id
            WHERE
                b.city_id = %s
                AND DATE(b.last_updated AT TIME ZONE cc.city_tz) = %s
            GROUP BY
                DATE_TRUNC('minute', b.last_updated AT TIME ZONE cc.city_tz), b.station_number
        ),
        distinct_minutes AS (
            SELECT DISTINCT DATE_TRUNC('minute', b.last_updated AT TIME ZONE cc.city_tz) AS minute
            FROM public.bikes b
            JOIN city_context cc ON cc.city_id = b.city_id
            WHERE
                b.city_id = %s
                AND DATE(b.last_updated AT TIME ZONE cc.city_tz) = %s
        ),
        station_minute_combinations AS (
            SELECT
                dm.minute,
                fs.id,
                fs.uid,
                fs.latitude,
                fs.longitude,
                fs.name,
                fs.spot,
                fs.station_number,
                fs.maintenance,
                fs.terminal_type,
                fs.city_id,
                fs.city_name
            FROM
                distinct_minutes dm
            CROSS JOIN
                filtered_stations fs
        ),
        station_bike_combined AS (
            SELECT
                smc.minute,
                smc.id,
                smc.uid,
                smc.latitude,
                smc.longitude,
                smc.name,
                smc.spot,
                smc.station_number,
                smc.maintenance,
                smc.terminal_type,
                smc.city_id,
                smc.city_name,
                COALESCE(bd.bike_count, 0) AS bike_count,
                COALESCE(bd.bike_list, '') AS bike_list
            FROM
                station_minute_combinations smc
            LEFT JOIN
                bike_data bd
            ON
                smc.station_number = bd.station_number
                AND smc.minute = bd.minute
        ),
        bike_changes AS (
            SELECT
                sbc.*,
                LAG(bike_count) OVER (PARTITION BY station_number ORDER BY minute) AS previous_bike_count
            FROM
                station_bike_combined sbc
        ),
        filtered_changes AS (
            SELECT
                *
            FROM
                bike_changes
            WHERE
                bike_count IS DISTINCT FROM previous_bike_count
        )
        SELECT
            minute,
            id,
            uid,
            latitude,
            longitude,
            name,
            spot,
            station_number,
            maintenance,
            terminal_type,
            city_id,
            city_name,
            bike_count,
            bike_list
        FROM
            filtered_changes
        ORDER BY
            station_number, minute;

    """
    city_timezone = "UTC"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(timezone, 'UTC') FROM public.cities WHERE city_id = %s",
                (city_id,),
            )
            row = cur.fetchone()
            city_timezone = row[0] if row else "UTC"

        df = pd.read_sql_query(
            query,
            conn,
            params=(city_id, city_id, date, city_id, date, city_id, date),
        )

    city_zone = ZoneInfo(city_timezone)
    df["minute"] = pd.to_datetime(df["minute"]).map(
        lambda timestamp: timestamp.replace(tzinfo=city_zone).isoformat(timespec="seconds")
    )
    df["timezone"] = city_timezone
    return df


def process_and_save_stations(city_id, date, folder, export_files=False):
    df = fetch_station_data(city_id, date)
    if export_files:
        save_gzipped_csv(os.path.join(folder, f"{city_id}_stations_{date}.csv.gz"), df)
