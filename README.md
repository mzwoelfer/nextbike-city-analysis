<div align="center" width="100%">
    <h2>Nextbike city analysis</h2>
    <p>NextBike trip analysis for your city. Collect, process and visualize bike trips in your City.</p>
</div>

This project pulls data from the public Nextbike API and aggreagtes it into "trips". Then the data can be previewed on a map.
Or you can use the data in csv format to do your own analysis in Excel.

## Overview

```SHELL
- collection/           # Setup Nextbike API data collection on a server
- data/                 # Nextbike trips data
- docs/                 # Documentation
- processing/           # Calculate trips from data in database
- visualization/        # Webpage to visualize the trips
```

### Prerequisites

- Docker (for containerized setup. See [Install Docker](https://docs.docker.com/engine/install/))
- Python 3.12

#### Development
1. Clone Repository: `git clone git@github.com:zwoefler/nextbike-city-analysis.git`
2. Change directory: `cd nextbike-city-analysis/`
3. Change into directory for development. `collection/` or `processing/`
4. Create python virtual environment:
```SHELL
python3 -m venv Env
source Env/bin/activate
pip install -r requirements.txt
```

## 🚀 Getting started / Install
1. Clone repo:
```SHELL
git clone https://github.com/zwoefler/nextbike-city-analysis.git
cd nextbike-city-analysis
```

2. Setup data collection:
```SHELL
# Change directory into collection
cd collection

# Copy the fake env vars
cp .env.example .env

# Start data aggregation in background. Pulls & builds the images
docker compose --file docker-compose.yaml up -d

# cd back to project root
cd ..
```

3. Set city_id and date to today as shell variables:
```SHELL
# Use format YYYY-MM-DD.
date='2025-01-07'
city_id=467
```

4. Calculate trips (Wait a few minutes before execution):
```SHELL
cd data_processing

python3 -m nextbike_processing.main --city-id $city_id --export-folder ../data/trips_data/ --date $date

cd ..
```

5. Visualize trips:

```SHELL
# Copy data to visualization data
cp "data/trips_data/${city_id}_trips_${date}.json" visualization/data/
cp "data/trips_data/${city_id}_stations_${date}.json" visualization/data/
```

Change into `visualization/` and sstart the server to display the map:
```SHELL
python3 -m http.server 8000
```

6. Visit `localhost:8000` in your browser.

## Deploy to Github Pages
1. Update the data in the `data/` directory.
2. Run the `update-gh-pages.sh` script

Changes will sync with master. Only the `data/` directory will be pushed to the gh-pages branch. Not the master branch.

## Credits
Inspiration:
[36c3 - Verkehrswende selber hacken](https://www.youtube.com/watch?v=WhgRRpA3b2c) talk by
- [ubahnverleih](https://github.com/ubahnverleih) and
- [robbie5](https://github.com/robbi5)

🫵🏽 Check them out. An absolute treasure for mobility focused IT projects!


Technical inspiration from the great visualization by [Technologiestiftung Berlin](https://github.com/technologiestiftung).
Especially their two projects:
- [Bike-Sharing](https://github.com/technologiestiftung/bike-sharing)
- [Bikesharing-Vis](https://github.com/technologiestiftung/bikesharing-vis)

