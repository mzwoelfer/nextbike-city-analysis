# Analyzing Nextbike data

Nextbike data is in postgres databases, with the format you can see [here](../create_bike_and_stations_db.sql)


The raw bikes data has timetamps and location data.
For analysis, we extract "trips".
Trips are the difference in time and location for the same bike.


## Run analysis
- Activate Python3 virtual env
- cd `nextbike-city-analysis/src/analysis`
- Install python dependencies: `pip install -r requirements.txt`

1. Add your postgres credentials into `config.py`
2. Calculate the trips: `python3 calculate_trips.py ../../data/trips_2024-11-06.csv`
3. Show trips: `python3 plot_trips.py`

---

## Create Trips
```SQL
WITH bike_movements AS (
    SELECT bike_number,
           latitude AS start_latitude,
           longitude AS start_longitude,
           last_updated AS start_time,
           LEAD(latitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_latitude,
           LEAD(longitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_longitude,
           LEAD(last_updated) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_time
    FROM public.bikes
)

SELECT bike_number,
       start_latitude,
       start_longitude,
       start_time,
       end_latitude,
       end_longitude,
       end_time
FROM bike_movements
WHERE end_latitude IS NOT NULL -- Exclude last record per bike. has no "next" entry
  AND (start_latitude != end_latitude OR start_longitude != end_longitude)
ORDER BY bike_number, start_time;
```


