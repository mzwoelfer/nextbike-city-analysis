import os
import pandas as pd
from nextbike_processing.database import get_connection
from nextbike_processing.utils import save_csv, save_json


def fetch_station_data(city_id, date):
    query = f"""
    WITH station_data AS (
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
                    PARTITION BY uid, latitude, longitude, name, spot, station_number, terminal_type, DATE(last_updated), maintenance
                    ORDER BY last_updated DESC
                ) AS rn
            FROM public.stations
            WHERE city_id = {city_id}
            AND DATE(last_updated) = '{date}'
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
                DATE_TRUNC('minute', b.last_updated) AS minute,
                b.station_number,
                COUNT(b.bike_number) AS bike_count,
                STRING_AGG(b.bike_number::TEXT, ', ') AS bike_list
            FROM
                public.bikes b
            WHERE
                city_id = {city_id}
                AND DATE(b.last_updated) = '{date}'
            GROUP BY
                DATE_TRUNC('minute', b.last_updated), b.station_number
        ),
        distinct_minutes AS (
            SELECT DISTINCT DATE_TRUNC('minute', b.last_updated) AS minute
            FROM public.bikes b
            WHERE
                city_id = {city_id}
                AND DATE(b.last_updated) = '{date}'
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
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn)
    df["minute"] = pd.to_datetime(df["minute"]).dt.strftime("%Y-%m-%dT%H:%M:%S")
    return df


def process_and_save_stations(city_id, date, folder):
    df = fetch_station_data(city_id, date)
    save_json(
        os.path.join(folder, f"{city_id}_stations_{date}.json"),
        df.to_dict(orient="records"),
    )
    save_csv(os.path.join(folder, f"{city_id}_stations_{date}.csv"), df)
