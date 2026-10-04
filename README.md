<div align="center" width="100%">
    <h2>Nextbike City Analysis</h2>
    <p>Analyze NextBike trips in your city: collect, process, and visualize bike trips.</p>
</div>

## Quick Start

Prerequisite: Docker with the Compose plugin ([installation guide](https://docs.docker.com/engine/install/)).

1. Clone the repository and enter it:
   ```sh
   git clone https://github.com/zwoefler/nextbike-city-analysis.git
   cd nextbike-city-analysis
   ```
2. Create local configuration and set a private database password and the city IDs to collect:
   ```sh
   cp .env.example .env
   ```
   Find city IDs in [`city_ids_2026_10_04.md`](city_ids_2026_10_04.md). Configuration details are in [deployment and data contract](docs/deployment-and-data-contract.md).
3. Build and start the services:
   ```sh
   docker compose up -d --build
   ```
4. Open `http://localhost:8080` (or the configured `VISUALIZATION_PORT`). The collector polls once per minute. Scheduled trip processing runs at midnight; for immediate or historical processing, follow [manual processing](docs/manual-processing.md).

The stack contains PostgreSQL, the collector, the scheduled processor, and the FastAPI visualization. The processor stores trips and cached OSM routes in PostgreSQL. Optional trip GeoJSON exports can be written with `--export-files`; the visualization reads processed data from the database-backed API.

## Stop / destroy

```sh
# Stop containers
docker compose down

# Stop and permanently delete all data (including the database volume)
docker compose down -v --remove-orphans
```

## Credits
Inspired by [36c3 - Verkehrswende selber hacken](https://www.youtube.com/watch?v=WhgRRpA3b2c) by [ubahnverleih](https://github.com/ubahnverleih) & [robbie5](https://github.com/robbi5).

Visualization inspired by [Technologiestiftung Berlin](https://github.com/technologiestiftung):
- [Bike-Sharing](https://github.com/technologiestiftung/bike-sharing)
- [Bikesharing-Vis](https://github.com/technologiestiftung/bikesharing-vis)

