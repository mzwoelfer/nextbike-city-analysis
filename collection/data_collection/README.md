# Nextbike Data Collection

A Python CLI tool for collecting bike and station data from the Nextbike API.

## Usage

### Quick Test (No Database Required)
```bash
python3 query_nextbike.py --city-ids 467
```
Fetches and displays bike/station data for specified cities without saving to database.

### Production Mode (Requires Database)
```bash
python3 query_nextbike.py --city-ids 467 --save
```
Fetches data and saves to PostgreSQL database.

### Environment Configuration
Create a `.env` file for automated runs:
```bash
DB_HOST=postgres
DB_PORT=5432
DB_NAME=nextbike_data
DB_USER=bike_admin
DB_PASSWORD=mybike
CITY_IDS=467

# Custom table names (defaults shown)
DB_CITIES_TABLE=public.cities
DB_BIKES_TABLE=public.bikes
DB_STATIONS_TABLE=public.stations
```

Then run without arguments:
```bash
python3 query_nextbike.py --save
```

## CLI Options
- `--city-ids`: Space-separated city IDs to fetch (overrides .env CITY_IDS)
- `--save`: Save data to database 

## Run tests
From `collection/data_collection`, run the unit tests:

```sh
python3 -m unittest discover -s tests
```

The PostgreSQL integration tests run when `TEST_DATABASE_URL` points to a dedicated test database. Initialize it with the collection schema before running the suite:

```sh
export TEST_DATABASE_URL=postgresql://user:password@localhost:5432/nextbike_test
psql "$TEST_DATABASE_URL" -f ../create_bike_and_stations_db.sql
python3 -m unittest discover -s tests
```

Do not point `TEST_DATABASE_URL` at production; tests clean up their own inserted rows.

#### Run coverage tests
From `collection/data_collection`, install requirements and run coverage:
```bash
python3 -m pip install -r requirements.txt
python3 -m coverage run --source=database,query_nextbike -m unittest discover -s tests
python3 -m coverage report --show-missing
```
