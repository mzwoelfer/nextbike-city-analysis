# Manual trip processing

The `processor` service runs automatically at midnight.
It calculates the previous day's trips for every city in `CITY_IDS`. 
Use the steps below to trigger processing on demand - for a specific city, date, or to backfill historical data.

## Prerequisites

- Stack runs (`docker compose up -d`)
- `postgres` container is contains raw bike data for the date you want to process
- `.env` file is present in the project root

## Run the processor manually

```sh
nerdctl run --rm \
  --env-file .env \
  --network nextbike-city-analysis_nextbike_network \
  -v nextbike-city-analysis_trip_data:/data \
  nextbike-city-analysis-processor \
  --city-id <CITY_ID> --export-folder /data --date <YYYY-MM-DD>
```

The processor image has `ENTRYPOINT ["python", "-m", "nextbike_processing.main"]`, so pass only the arguments - not the python command itself.


Example for city 467, processing 30 May 2026:

```sh
nerdctl run --rm \
  --env-file .env \
  --network nextbike-city-analysis_nextbike_network \
  -v nextbike-city-analysis_trip_data:/data \
  nextbike-city-analysis-processor \
  --city-id 467 --export-folder /data --date 2026-05-30
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--city-id` | yes | Nextbike city ID (see [`city_ids_2025_02_15.md`](../city_ids_2025_02_15.md)) |
| `--export-folder` | yes | Output folder inside the container. Use `/data` to write to the shared volume. |
| `--date` | yes | Date in `YYYY-MM-DD` format |

### Output files

Two gzipped CSV files are written to the `trip_data` volume:

```
/data/{city_id}_trips_{date}.csv.gz
/data/{city_id}_stations_{date}.csv.gz
```

## Update the visualization

The webapp reads `data/manifest.json` to discover available files. 
After processing, regenerate it:

```sh
nerdctl exec nextbike_visualization sh -c "cd /app/data && sh /app/create_manifest.sh"
```

Then refresh the browser. The new date will appear in the date selector.

## Backfill multiple dates

To process a range of dates for a single city, loop over the dates in your shell:

```sh
for date in 2026-05-28 2026-05-29 2026-05-30; do
  nerdctl run --rm \
    --env-file .env \
    --network nextbike-city-analysis_nextbike_network \
    -v nextbike-city-analysis_trip_data:/data \
    nextbike-city-analysis-processor \
    --city-id 467 --export-folder /data --date "$date"
done
```

Run the manifest update once after the loop completes.

## Notes

- Running the processor twice overwrites the output files. No deduplication in the current setup.
- The processor downloads the OSM road network for the city on every run (10 km radius). This is memory-intensive and takes a minute or two. 
- Use `--env-file .env` - not `nerdctl compose run` - as `nerdctl compose` ignores `env_file` and the container will start without database credentials.
