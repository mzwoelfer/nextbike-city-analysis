# Nextbike Visualization

Interactive map. VIzualizes trips for Nextbike data. 
- FastAPI. port 8080.

## Architecture

```
Browser → FastAPI (api.py) → PostgreSQL
                ↓
         /app (static files: index.html, CSS, JS)
         /app/data (optional static CSV bundle)
```

The frontend detects whether the API is available:

- **API mode** (production): queries trip, station, and bike data from database via `/api/*` endpoints.
- **Static mode** (GitHub Pages / local dev): discovers trip and station CSV files, plus optional `*_bikes_*.csv.gz` files, from `data/manifest.json`. Static mode does not load GeoJSON files.

The public GitHub Pages site uses bundled sample CSV files; it does not connect to a public live database. See the [deployment and data contract](../docs/deployment-and-data-contract.md) for file schemas and onboarding.

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /api/available` | List of `{city_id, dates}` with processed data |
| `GET /api/trips?city_id=X&date=Y` | GeoJSON FeatureCollection of trips for a given city and date |
| `GET /api/bikes?city_id=X&date=Y` | Time-indexed bike observations for bikes that are unassigned at some point that day |
| `GET /api/stations?city_id=X&date=Y` | Station bike-count and bike-type timeline (one row per station per change) |

## Production

Starts automatically with the root compose stack:
```sh
docker compose up -d
```

Visit `http://localhost:8080` (or the port set by `VISUALIZATION_PORT` in `.env`).

## Tests and coverage

From `visualization/`, install requirements and run the API tests with coverage:

```sh
python3 -m pip install -r requirements.txt
python3 -m coverage run --source=api -m unittest discover -s tests
python3 -m coverage report --show-missing
```

The HTTP validation and timezone tests run without PostgreSQL. Endpoint integration tests run only when `DB_NAME=nextbike_api_test`; they create and remove fixture records in that database. Point these tests only at a disposable PostgreSQL database. CI starts an isolated PostgreSQL service for them.

## Updating the visualization container
```sh
docker compose up -d --no-deps --build visualization
```

## Local development (static mode, no Docker)

```sh
cd visualization/
python3 -m http.server 8000
```

Open `http://localhost:8000`. 
Trip and station data must be present in `visualization/data/` as `.csv.gz` files. Bike CSVs are optional; without them, the visualization shows no standalone-bike markers.
Generate a manifest so the file listing works without directory listing support:
```sh
bash create_manifest.sh
```

## Deployment on GitHub Pages

GitHub Pages does not support directory listing. Therefore `manifest.json` in `visualization/data/` lists available data files for the frontend to discover.

The manifest is generated automatically in the GitHub Actions workflow that publishes to GitHub Pages.
