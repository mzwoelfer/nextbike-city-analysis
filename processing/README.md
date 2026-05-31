# Nextbike Trip Processing

Extracts bike trips from the raw polling data in PostgreSQL, calculates routes via OpenStreetMap, and writes the results back to the database and to compressed GeoJSON files.

## How it works

For a given city and date:

1. Reads raw `bikes` and `stations` records from PostgreSQL
2. Calculates trips between stations.
3. Calculates the road-network trip-routes using OSMnx.
   - Caches calcualted trip-routes in the `public.routes` table. 
   - reuses cached geometry. REduces calls to OSMnx
4. Writes the results to:
   - `public.trips`
   - `{city_id}_trips_{date}.geojson.gz` on the shared `trip_data` volume (for static/GitHub Pages fallback).

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
        "coordinates": [[13.400, 52.500], [13.401, 52.501]]
      },
      "properties": {
        "bike_number": "42",
        "start_time": "2026-05-30T08:14:00",
        "end_time": "2026-05-30T08:27:00",
        "duration": 780,
        "distance": 1240.5,
        "timestamps": ["2026-05-30T08:14:00", "2026-05-30T08:27:00"]
      }
    }
  ]
}
```

GeoJSON coordinates are `[longitude, latitude]` (x, y order).

## Production

The processor runs automatically at midnight every day for each city in `CITY_IDS`:
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
docker compose up -d --no-deps --build processor
```