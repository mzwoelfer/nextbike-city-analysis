<div align="center" width="100%">
    <h2>Nextbike City Analysis</h2>
    <p>Analyze NextBike trips in your city: collect, process, and visualize bike trips.</p>
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
- Docker ([Install Docker](https://docs.docker.com/engine/install/))
- Python 3.12

## 🚀 Validation setup (Not for production)

This setup is only for local validation that the project works.
For proper setup of data collection and processing, refer to the README files in `collection/` and `processing/` directories.

1. Clone repository:
   ```sh
   git clone https://github.com/zwoefler/nextbike-city-analysis.git
   cd nextbike-city-analysis
   ```
2. Setup data collection:
   ```sh
   cd collection
   cp .env.example .env 
   docker build --file CONTAINERFILE -t nextbike_collector:multiple_cities .
   docker compose --file docker-compose.yaml up -d
   cd ..
   ```
3. Define city and date:
   ```sh
   # Sets todays date
   date=$(date +%Y-%m-%d)
   city_id=467
   ```
4. Process trips:
   ```sh
   cd processing
   cp .env.example .env 
   docker build --file CONTAINERFILE -t nextbike-processing:latest .
   docker run --rm --env-file .env \
      -e DB_HOST=nextbike_postgres \
      --network collection_nextbike_network \
      -v "$(pwd)/../data/:/app/data" \
      nextbike-processing:latest \
      --city-id $city_id --export-folder /app/data --date $date

   cd ..
   ```
5. Visualize trips:
   ```sh
   cd visualization 
   python3 -m http.server 8000
   ```
6. Open `localhost:8000` in your browser.

## Credits
Inspired by [36c3 - Verkehrswende selber hacken](https://www.youtube.com/watch?v=WhgRRpA3b2c) by [ubahnverleih](https://github.com/ubahnverleih) & [robbie5](https://github.com/robbi5).

Visualization inspired by [Technologiestiftung Berlin](https://github.com/technologiestiftung):
- [Bike-Sharing](https://github.com/technologiestiftung/bike-sharing)
- [Bikesharing-Vis](https://github.com/technologiestiftung/bikesharing-vis)

