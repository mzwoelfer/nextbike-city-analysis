# Analyzing Nextbike data

Nextbike data is in postgres databases.

The raw bikes data has timetamps and location data.
For analysis, we extract "trips".
Trips are the difference in time and location for the same bike.



## Build Image
```SHELL
project_address=($PWD)
city_id=467
cd processing

# Build Image
nerdctl build --file CONTAINERFILE -t nb_processing .

# Run and pull data from local postgres
nerdctl run --rm --env-file .env nb_processing

nerdctl run --rm -v "$project_address/data/trips_data/:/app/export" --network collection_nextbike_network --env-file .env nb_processing:latest --export-folder /app/export --city-id "$city_id"
```

## Local Development
```SHELL
project_address=($PWD)
cd processing

source Env/bin/activate
pip install -r requirements.txt
```

ADD YOUR CITY ID:
```SHELL
python3 calculate_trips.py --city-id <CITY_ID> --export-folder test_data/
python3 pull_stations.py --city-id <CITY_ID> --export-folder test_data/
```


## Run analysis - Python
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


## Tips for the future
#### Avoid using alpine python base images
Alpine uncompressed is smaller than most images out there.
But you get (especially for more python dependencies):
- less compatibility
- acutally bigger images
- longer build times
- more hustle.

The smallest I could get with `alpine` was 783.7 MB.
With the `slim` image: 745.8MB.

Just use a Debian or Redhat slim base image like:
`python:3.12.7-slim-bullseye`
