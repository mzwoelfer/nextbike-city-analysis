# Manual trip processing

The `processor` service runs automatically at midnight.
It calculates the previous day's trips for every city in `CITY_IDS`.
Use the steps below to trigger processing on demand  for a specific city, date, or to backfill historical data.

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

- `env-file`: your env file in repos root
- `--network`: The full network name created by nerdctl using the [roots docker compose](../docker-compose.yaml).
- `nextbike-city-analysis-processor`: full name to processor image build by the projects root `docker-compose.yaml`
- `--city-id`: your city id (also defined in `.env`)
- `--date`: date in ISO-8601 date only timestamp[1]


Example for city 467, processing 30 May 2026:

```sh
docker run --rm \
  --env-file .env \
  --network nextbike-city-analysis_nextbike_network \
  nextbike-city-analysis-processor \
  --city-id 467 --date 2026-05-30
```

## Process all configured cities today

Run from the repository root. This reads comma-separated `CITY_IDS` from `.env` and processes each city for today's date:

```sh
process_date=$(date +%F)
docker compose run --rm --no-deps \
  -e PROCESS_DATE="$process_date" \
  --entrypoint sh processor -c '
    set -eu
    : "${CITY_IDS:?Set CITY_IDS in .env}"
    for city_id in $(printf "%s" "$CITY_IDS" | tr "," " "); do
      printf "Processing city %s for %s\n" "$city_id" "$PROCESS_DATE"
      python -m nextbike_processing.main --city-id "$city_id" --date "$PROCESS_DATE"
    done
  '
```

## Export trip GeoJSON

Add `--export-files` and `--export-folder` to write compressed GeoJSON to the shared volume:

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
```

## Arguments

| Argument | Required | Description |
|---|---|---|
| `--city-id` | yes | Nextbike city ID (see [`city_ids_2026_10_04.md`](../city_ids_2026_10_04.md)) |
| `--date` | yes | Date in `YYYY-MM-DD` format |
| `--export-files` | no | Also write a `.geojson.gz` trip file |
| `--export-folder` | no* | Output folder inside the container. Required when `--export-files` is set. |

The processor image has `ENTRYPOINT ["python", "-m", "nextbike_processing.main"]`, so pass only the arguments.

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


## SOURCES
[1] ISO 8601 - Date and time format; iso.org; https://www.iso.org/iso-8601-date-and-time-format.html (2026-07-10)