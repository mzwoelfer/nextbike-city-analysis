# Nextbike Trip Processing

Extracts bike trips from raw polling data in PostgreSQL and calculates routes via OpenStreetMap. The scheduled processor writes to PostgreSQL; file exports are opt-in.

## How it works

For a given city and date:

1. Reads raw `bikes` and `stations` records from PostgreSQL
2. Calculates trips between stations.
3. Calculates the road-network trip-routes using OSMnx.
  - Caches calculated trip routes in the `public.routes` table.
  - Reuses cached geometry to reduce calls to OSMnx.
4. Writes trips and available route references to `public.trips`. Failed route lookups do not provide route geometry.
5. With `--export-files`, writes `{city_id}_trips_{date}.geojson.gz` and `{city_id}_trips_{date}.csv.gz` to the requested export folder. Station exports use `{city_id}_stations_{date}.csv.gz`.

## Output format

Trips are in a **GeoJSON FeatureCollection** (gzip-compressed):

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [13.4, 52.5],
          [13.401, 52.501]
        ]
      },
      "properties": {
        "bike_number": "42",
        "start_time": "2026-05-30T08:14:00",
        "end_time": "2026-05-30T08:27:00",
        "duration": 780,
        "distance": 1240.5,
        "timezone": "Europe/Berlin"
      }
    }
  ]
}
```

GeoJSON coordinates are `[longitude, latitude]` (x, y order).

## Production

The processor runs automatically at midnight for each city in `CITY_IDS`. The Compose schedule processes to PostgreSQL and does not enable file export:

```sh
# From the project root
docker compose up -d
```

## Manual processing

To process a specific city and date on demand (DB only, no files):

```sh
docker run --rm \
  --env-file .env \
  --network nextbike-city-analysis_nextbike_network \
  nextbike-city-analysis-processor \
  --city-id 467 --date 2026-05-31
```

To write the data to files (`.geojson.gz` / `.csv.gz`) for GitHub Pages or local testing, add `--export-files`:

```sh
docker run --rm \
  --env-file .env \
  --network nextbike-city-analysis_nextbike_network \
  -v nextbike-city-analysis_trip_data:/data \
  nextbike-city-analysis-processor \
  --city-id 467 --date 2026-05-31 --export-files --export-folder /data
```

## Updating the processor image

```sh
docker compose up -d --build processor
```

## Running tests

```sh
cd processing/
python3 -m venv Env
source Env/bin/activate
pip install -r requirements.txt pytest
pytest tests/ -v
```

## Measuring test coverage

From `processing/`, run the unittest suite under coverage and show uncovered lines:

```sh
python -m coverage run --source=nextbike_processing -m unittest discover -s tests
python -m coverage report --show-missing
```

