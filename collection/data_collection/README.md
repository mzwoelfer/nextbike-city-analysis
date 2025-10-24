# Nextbike Data Collection

A Python CLI tool for collecting bike and station data from the Nextbike API.

## Usage

### Quick Test (No Database Required)
```bash
python query_nextbike.py --city-ids 467
```
Fetches and displays bike/station data for specified cities without saving to database.

### Production Mode (Requires Database)
```bash
python query_nextbike.py --city-ids 467 --save
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
python query_nextbike.py --save
```

## CLI Options
- `--city-ids`: Space-separated city IDs to fetch (overrides .env CITY_IDS)
- `--save`: Save data to database 