# Deployment and Data Contract

## Data Flow

- Collector polls Nextbike every 60 seconds and writes bike and station observations to PostgreSQL.
- Processor runs at midnight for the previous day and writes trips to `public.trips` and routes to `public.routes` ([manual processing](manual-processing.md)).
- A trip can exist without a route if routing fails.
- The visualization serves the UI and the API below, reading from PostgreSQL.

## Live API

All endpoints except `/api/available` take `city_id` and `date` (`YYYY-MM-DD`).

- `GET /api/available`: cities with processed dates, e.g. `[{"city_id": "467", "city_name": "Giessen", "dates": ["2026-10-04"]}]`. Empty until trips are processed.
- `GET /api/trips`: GeoJSON FeatureCollection. Properties: bike number, start/end time, duration (s), distance (m), route ID, timezone. Coordinates are `[longitude, latitude]`. Unrouted trips have `route_id: null`, empty coordinates, and distance `0`.
- `GET /api/stations`: station observations with metadata, bike count, bike list, and raw type counts. Only change points, not repeated rows.
- `GET /api/bikes`: minute-indexed observations for bikes unassigned at some point that day (coordinates, station, raw `bike_type`).

Notes:
- Timestamps are ISO 8601 with the city's UTC offset.
- Optional trip export: processor `--export-files` with `--export-folder`.
