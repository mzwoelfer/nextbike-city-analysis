<div align="center" width="100%">
    <h2>Nextbike City Analysis</h2>
    <p>Analyze NextBike trips in your city: collect, process, and visualize bike trips.</p>
    <p><a href="https://mzwoelfer.github.io/nextbike-city-analysis/">🔴 Live Preview</a></p>
</div>

## Overview

```SHELL
- collection/       # Setup data collection
- data/             # Stored trips data
- docs/             # Documentation
- processing/       # Calculate trips
- visualization/    # Web visualization
```

## Prerequisites
- Docker with Compose ([Install Docker](https://docs.docker.com/engine/install/))

## 🚀 Install

1. Clone the repository:
   ```sh
   git clone https://github.com/zwoefler/nextbike-city-analysis.git
   cd nextbike-city-analysis
   ```

2. Create your `.env` file:
   ```sh
   cp .env.example .env
   ```
   Edit `.env` and set your values:

   | Variable | Description |
   |---|---|
   | `DB_USER` | Postgres username |
   | `DB_PASSWORD` | Postgres password |
   | `DB_NAME` | Postgres database name |
   | `DB_HOST` | Postgres host (`nextbike_postgres` when using compose) |
   | `DB_PORT` | Postgres port (default: `5432`) |
   | `DB_BIKES_TABLE` | Table name for raw bike data |
   | `DB_STATIONS_TABLE` | Table name for station data |
   | `DB_CITIES_TABLE` | Table name for city data |
   | `CITY_IDS` | Comma-separated Nextbike city IDs to collect, e.g. `467,210` |
   | `STATIONS_SYNC_INTERVAL_HOURS` | How often to sync stations |
   | `CITIES_SYNC_INTERVAL_HOURS` | How often to sync city metadata |
   | `EXPORT_DIR` | Output folder for processed trip files (default: `/data`) |
   | `VISUALIZATION_PORT` | Port for the web UI (default: `8080`) |

   Find your city ID in [`city_ids_2025_02_15.md`](city_ids_2025_02_15.md).

3. Start everything:
   ```sh
   docker compose up -d
   ```

   This starts four services:
   - **postgres** - database for raw bike and station data
   - **collector** - polls the Nextbike API every 60 seconds and writes to postgres
   - **processor** - runs at midnight, calculates trips for each city in `CITY_IDS` and writes to `/data`
   - **visualization** - serves the web UI at `http://localhost:${VISUALIZATION_PORT}`

4. Open `http://localhost:8080` (or your configured `VISUALIZATION_PORT`) in your browser.

   > ⚠ Trip data appears the day after collection starts - the processor runs at midnight on yesterday's data. To trigger processing manually, see [docs/manual-processing.md](docs/manual-processing.md).

## Stop / destroy

```sh
# Stop containers
docker compose down

# Stop and delete all data (including the database volume)
docker compose down -v --remove-orphans
```

## Credits
Inspired by [36c3 - Verkehrswende selber hacken](https://www.youtube.com/watch?v=WhgRRpA3b2c) by [ubahnverleih](https://github.com/ubahnverleih) & [robbie5](https://github.com/robbi5).

Visualization inspired by [Technologiestiftung Berlin](https://github.com/technologiestiftung):
- [Bike-Sharing](https://github.com/technologiestiftung/bike-sharing)
- [Bikesharing-Vis](https://github.com/technologiestiftung/bikesharing-vis)

