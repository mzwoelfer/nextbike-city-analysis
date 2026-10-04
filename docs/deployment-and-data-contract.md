# Deployment and Data Contract

## Onboarding

1. Install Docker Engine with the Compose plugin.
2. Copy `.env.example` to `.env`. Set a private `DB_PASSWORD` and choose one or more Nextbike IDs in `CITY_IDS`, separated by commas. The repository's city list is a starting point; confirm the current ID with Nextbike before deploying.
3. Start the stack from the repository root:

   ```sh
   docker compose up -d --build
   ```

4. Open `http://localhost:8080`, or the configured `VISUALIZATION_PORT`. The collector polls every 60 seconds. The processor handles the previous day at midnight, so an initially empty visualization is expected until trips have been processed. Use [manual processing](manual-processing.md) to process a date immediately or export static files.

The stack runs PostgreSQL, a collector, a midnight processor, and the FastAPI visualization. Keep `.env` private. The default database port is `5432`; the visualization port defaults to `8080`.

To check which city dates are ready, request `http://localhost:8080/api/available`. An empty list means no trip data has been processed yet. `docker compose down` stops services but keeps database and export volumes; `docker compose down -v` deletes those volumes.

## Data Flow

The collector stores Nextbike bike and station observations in PostgreSQL. The processor detects trips, caches routed station pairs in `public.routes`, and stores trip records in `public.trips`. Route calculation can fail independently of trip detection: a trip may exist without a route ID or geometry.

The live visualization reads from the API. The GitHub Pages visualization is a separate static demo using bundled sample CSV data; it does not connect to the project's database.

## Live API

`GET /api/available` returns city IDs, display names, and processed local dates:

```json
[
  {"city_id": "467", "city_name": "Giessen", "dates": ["2026-10-04"]}
]
```

`GET /api/trips?city_id=467&date=2026-10-04` returns a GeoJSON FeatureCollection. Each feature has bike number, start and end timestamps, duration in seconds, distance in meters, route ID, and timezone. GeoJSON coordinates use `[longitude, latitude]` order. When routing failed, the trip remains in the response with `route_id: null` and an empty coordinate array; the API reports distance as `0` when no route distance exists.

`GET /api/stations?city_id=467&date=2026-10-04` returns station observations with minute, station identifiers and coordinates, station metadata, bike count, bike list, raw bike-type counts, and timezone. Bike counts and type counts are change points rather than repeated rows for unchanged minutes.

`GET /api/bikes?city_id=467&date=2026-10-04` returns minute-indexed observations for bikes that are unassigned at some point that day. Each observation includes bike number, coordinates, station assignment, raw `bike_type`, minute, and timezone. The visualization shows these bikes only while unassigned and synchronizes them with playback.

## Static CSV Bundle

Static mode reads `data/manifest.json`, which lists available filenames. Trip files use `{city_id}_trips_{date}.csv.gz`; station files use `{city_id}_stations_{date}.csv.gz`.

Trip CSV columns, in order: `bike_number`, `start_latitude`, `start_longitude`, `start_time`, `end_latitude`, `end_longitude`, `end_time`, `duration`, `date`, `distance`, `segments`, `route_id`, `timezone`.

Station CSV columns: `minute`, `id`, `uid`, `latitude`, `longitude`, `name`, `spot`, `station_number`, `maintenance`, `terminal_type`, `city_id`, `city_name`, `bike_count`, `bike_list`, `bike_type_counts`, `timezone`.

Bike CSV files use `{city_id}_bikes_{date}.csv.gz` and contain `minute`, `bike_number`, `latitude`, `longitude`, `station_number`, `bike_type`, and `timezone`. Older static bundles without bike files remain valid; they show station counts but no standalone bike markers.

The current bundled Pages sample has no bike CSV, so standalone-bike markers appear only where live bike data or a matching static bike file is available.

Timestamps are ISO 8601 with the city's UTC offset. Trip duration is seconds and distance is meters. Route segments are stored as coordinate pairs and converted to `[longitude, latitude]` for display. Empty route ID/segments indicate an unrouted trip. Static route IDs are grouped within an exported date and are not persistent database route IDs.

Use the processor's `--export-files` option to create trip files and `--export-folder` to choose their destination. The `EXPORT_DIR` entry in the environment template is historical and is not read by the current processor. The static site also needs station files and a regenerated manifest; GitHub Pages deployment packages its configured sample data automatically.
