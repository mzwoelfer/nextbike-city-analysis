<div align="center" width="100%">
    <h2>Nextbike city analysis</h2>
    <p>NextBike trip analysis for your city. Collect, process and visualize bike trips in your City.</p>
</div>

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

3. Calculate trips (Wait a few minutes before execution):
```SHELL
project_address=($PWD)
image_tag=nb_processing

cd data_processing

# Build Image
nerdctl build --file CONTAINERFILE -t $image_tag .

nerdctl run --rm \
    -v "$project_address/data/trips_data/:/app/export" \
    --network data_collection_nextbike_network \
    --env-file .env \
    $image_tag \
    --export /app/export

cd ..
```

4. Visualize trips:
🚧 TBD

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

