# TODO

## 1. Switch output format to GeoJSON

### Current approach
Trips are written as gzipped CSV files (`{city_id}_trips_{date}.csv.gz`). The `segments` column embeds coordinates and timestamps together as a list of `[lat, lon, timestamp]` tuples per row, serialised into the CSV cell:

```csv
bike_number,start_time,end_time,duration,segments,...
"42","2026-05-30T08:14:00","2026-05-30T08:27:00",780.0,"[[52.500,13.400,""2026-05-30T08:14:00""],[52.501,13.401,""2026-05-30T08:18:30""]]",...
```

This is sometimes called **M-values** or **4D coordinates** - extending the standard `[lon, lat]` GeoJSON position with a measure value (here: time). It is not part of the GeoJSON standard [1] and requires a hand-rolled CSV parser on the frontend.

### Target approach
Switch the processor output to **GeoJSON** (`{city_id}_trips_{date}.geojson.gz`). Each trip becomes a `Feature` with a `LineString` geometry and a parallel `timestamps` array in `properties`:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [13.400, 52.500],
          [13.401, 52.501],
          [13.403, 52.501]
        ]
      },
      "properties": {
        "bike_number": "42",
        "start_time": "2026-05-30T08:14:00",
        "end_time": "2026-05-30T08:27:00",
        "duration": 780,
        "distance": 1240.5,
        "timestamps": [
          "2026-05-30T08:14:00",
          "2026-05-30T08:18:30",
          "2026-05-30T08:27:00"
        ]
      }
    }
  ]
}
```

Note: GeoJSON coordinates are `[longitude, latitude]` (x, y order) - the reverse of Leaflet's `[lat, lon]`. Account for this when reading on the frontend.

Leaflet reads `FeatureCollection` natively via `L.geoJSON()`. The custom CSV parser in `visualization/scripts/data.js` can be removed.

---

## 2. Rework data storage: trips and routes tables in PostgreSQL

### Problem
- Trips and route geometry are only stored as files on a Docker volume - no queryability, no deduplication.
- The OSM route between two points (A → B) is recalculated from scratch on every run, even if that same origin/destination pair was processed before.
- Running the processor twice for the same date overwrites the output file; there is no idempotency.

### Target schema

```sql
CREATE TABLE IF NOT EXISTS public.routes (
    id SERIAL PRIMARY KEY,
    start_latitude DOUBLE PRECISION NOT NULL,
    start_longitude DOUBLE PRECISION NOT NULL,
    end_latitude DOUBLE PRECISION NOT NULL,
    end_longitude DOUBLE PRECISION NOT NULL,
    distance_meters DOUBLE PRECISION NOT NULL,
    coordinates JSONB NOT NULL,          -- [[lon, lat], ...]
    UNIQUE (start_latitude, start_longitude, end_latitude, end_longitude)
);

CREATE TABLE IF NOT EXISTS public.trips (
    id SERIAL PRIMARY KEY,
    bike_number TEXT NOT NULL,
    city_id INTEGER NOT NULL,
    start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    end_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    duration_seconds DOUBLE PRECISION NOT NULL,
    route_id INTEGER REFERENCES public.routes(id),
    timestamps JSONB NOT NULL,           -- ["2026-05-30T08:14:00", ...]
    UNIQUE (bike_number, city_id, start_time)
);
```

### Processing logic change
1. For each unique origin/destination pair, check `routes` first.
2. If found, reuse it - skip the OSMnx call.
3. If not found, calculate and insert with `INSERT ... ON CONFLICT DO NOTHING`.
4. Insert the trip with `INSERT ... ON CONFLICT DO NOTHING` - running the processor twice for the same date is safe.

This means OSMnx only runs for routes never seen before. Over time the route cache covers most of the city's common paths and processing becomes significantly faster.

---

## 3. Query the database for visualization

### Problem
- The visualization serves static `.csv.gz` files from a Docker volume via `python -m http.server`.
- New data is invisible until `create_manifest.sh` is run manually.
- No filtering, pagination, or on-demand processing is possible.

### Target approach
Replace the static file server with a **FastAPI** service that:

- Serves the existing HTML/CSS/JS as static files (same as now).
- Exposes a small API that the frontend calls instead of fetching files:

```
GET /api/cities
GET /api/trips?city_id=467&date=2026-05-30
POST /api/process?city_id=467&date=2026-05-30   ← manual trigger
```

The frontend fetches trips as GeoJSON directly from the API. No manifest, no volume, no manual step after processing.

FastAPI runs inside the existing `visualization` container - swap `python:3.11-alpine` for the processor image or a dedicated lightweight image with FastAPI + psycopg installed.

---

## Sources

[1] The GeoJSON Format. RFC 7946. <https://www.rfc-editor.org/rfc/rfc7946>
