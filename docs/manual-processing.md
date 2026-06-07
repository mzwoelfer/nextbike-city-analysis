# Manual trip processing

The `processor` service runs automatically at midnight.
It calculates the previous day's trips for every city in `CITY_IDS`.
Use the steps below to trigger processing on demand — for a specific city, date, or to backfill historical data.

## Prerequisites

- Stack is running (`docker compose up -d`)
- `postgres` container contains raw bike data for the date you want to process
- `.env` file is present in the project root

## Default: DB only (production)

By default the processor writes results to the database only (`public.trips` and `public.routes`):

```sh
docker run --rm \
  --env-file .env \
  --network nextbike-city-analysis_nextbike_network \
  nextbike-city-analysis-processor \
  --city-id <CITY_ID> --date <YYYY-MM-DD>
```

Example for city 467, processing 30 May 2026:

```sh
docker run --rm \
  --env-file .env \
  --network nextbike-city-analysis_nextbike_network \
  nextbike-city-analysis-processor \
  --city-id 467 --date 2026-05-30
```

## With static file export (GitHub Pages / local testing)

Add `--export-files` and `--export-folder` to also write `.geojson.gz` and `.csv.gz` to the shared volume:

```sh
docker run --rm \
  --env-file .env \
  --network nextbike-city-analysis_nextbike_network \
  -v nextbike-city-analysis_trip_data:/data \
  nextbike-city-analysis-processor \
  --city-id 467 --date 2026-05-30 --export-files --export-folder /data
```

Files written to the volume:
```
/data/{city_id}_trips_{date}.geojson.gz
/data/{city_id}_stations_{date}.csv.gz
```

After exporting files, regenerate the manifest so the webapp can discover them:
```sh
docker exec nextbike_visualization sh -c "cd /app/data && sh /app/create_manifest.sh"
```

## Arguments

| Argument | Required | Description |
|---|---|---|
| `--city-id` | yes | Nextbike city ID (see [`city_ids_2025_02_15.md`](../city_ids_2025_02_15.md)) |
| `--date` | yes | Date in `YYYY-MM-DD` format |
| `--export-files` | no | Also write static `.geojson.gz` / `.csv.gz` files |
| `--export-folder` | no* | Output folder inside the container. Required when `--export-files` is set. |

The processor image has `ENTRYPOINT ["python", "-m", "nextbike_processing.main"]`, so pass only the arguments — not the python command itself.

## Backfill multiple dates

```sh
for date in 2026-05-28 2026-05-29 2026-05-30; do
  docker run --rm \
    --env-file .env \
    --network nextbike-city-analysis_nextbike_network \
    nextbike-city-analysis-processor \
    --city-id 467 --date "$date"
done
```