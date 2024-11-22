#!/bin/bash

# CREATE A CRONJOB:
# crontab -e
# 0 0 * * * /path/to/your_script.sh

DB_NAME="nextbike_data"
DB_USER="bike_admin"
OUTPUT_DIR="/home/$USER"
TABLE_NAME="public.bikes"
CHECK_DIR="${OUTPUT_DIR}"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Fetch unique dates 
DATES=$(psql -U $DB_USER -d "$DB_NAME" -t -c "SELECT DISTINCT DATE(last_updated) FROM $TABLE_NAME ORDER BY DATE(last_updated);")

# Loop through dates
for DATE in $DATES
do
    OUTPUT_FILE="${OUTPUT_DIR}/trips_${DATE}.csv"

    if [ -f "$OUTPUT_FILE" ]; then
        echo "File $OUTPUT_FILE already exists. Skipping."
        continue
    fi

    SQL_QUERY="
    WITH bike_movements AS (
        SELECT 
            bike_number,
            latitude AS start_latitude,
            longitude AS start_longitude,
            last_updated AS start_time,
            LEAD(latitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_latitude,
            LEAD(longitude) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_longitude,
            LEAD(last_updated) OVER (PARTITION BY bike_number ORDER BY last_updated) AS end_time
        FROM $TABLE_NAME
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
        DATE(start_time) = '${DATE}'
        AND end_latitude IS NOT NULL
        AND (start_latitude != end_latitude OR start_longitude != end_longitude)
    ORDER BY 
        trip_date, 
        bike_number, 
        start_time
    "

    # Export the data
    echo "Exporting trips for $DATE..."
    echo "$OUTPUT_FILE"
    psql -U $DB_USER -d "$DB_NAME" -c "\COPY (${SQL_QUERY}) TO STDOUT WITH CSV HEADER;" > "$OUTPUT_FILE"

    echo "File $OUTPUT_FILE created."
done

echo "All exports completed."

