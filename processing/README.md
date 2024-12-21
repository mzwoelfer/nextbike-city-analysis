# Analyzing Nextbike data

Nextbike data is in postgres databases.

The raw bikes data has timetamps and location data.
For analysis, we extract "trips".
Trips are the difference in time and location for the same bike.



## Get trips data
1. Setup your environment
```SHELL
# Set variables
city_id=467
date='2024-12-21'

# Install requirements
python3 -m venv Env
source Env/bin/activate
pip install -r requirements.txt

# Copy the fake env vars
cp .env.example .env
```

2. Get your trips data
```SHELL
python3 -m nextbike_processing.main --city-id $city_id --export-folder ../data/trips_data/ --date $date
```

3. Trips data in `<PROJECT_ROOT>/data/trips_data/`
