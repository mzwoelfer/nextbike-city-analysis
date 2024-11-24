# Analyzing Nextbike data

Nextbike data is in postgres databases.

The raw bikes data has timetamps and location data.
For analysis, we extract "trips".
Trips are the difference in time and location for the same bike.

## Run analysis
- Activate Python3 virtual env
- cd `nextbike-city-analysis/data_processing`
- Install python dependencies: `pip install -r requirements.txt`

```SHELL
python3 -m venv Env
source Env/bin/activate
pip install -r requirements.txt

# Copy the fake env vars
cp .env.example .env

# Calculate the trips:
$ python3 calculate_trips.py ../data/raw/trips_2024-11-19.csv

# Output is in path `$PROJECT_ROOT/data/trips_data/trips_2024-11-19.json`

# Show trips:
python3 plot_trips.py
```


