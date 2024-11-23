# Database - Date extraction

A python script writes the Nextbike API data to a postgress database every minute.
🚧 WORK IN PROGRESS

Playbook:
1. Get the trips from database
2. calculate_trips.py from .csv
3. Multithread the calculate trip
4. visualization: put on map. Add timer,


1. Get trips from database. Use the `daily_trip_extractor.sh` script on the database server.

## Get the trips
```SQL
WITH bike_movements AS (
        SELECT
            bike_number,
            latitude AS start_latitude,
            longitude AS start_longitude,
            last_updated AS start_time,
            LEAD(latitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_latitude,
            LEAD(longitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_longitude,
            LEAD(last_updated) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_time
        FROM public.bikes
    )
    SELECT
        DATE(start_time) AS trip_date,
        bike_number,
        start_latitude,
        start_longitude,
        start_time,
        end_latitude,
        end_longitude,
        end_time
    FROM
        bike_movements
    WHERE
        DATE(start_time) = "2024-11-06"
        AND end_latitude IS NOT NULL
        AND (start_latitude != end_latitude OR start_longitude != end_longitude)
    ORDER BY
        trip_date,
        start_time,
        bike_number
    LIMIT 50;
```
