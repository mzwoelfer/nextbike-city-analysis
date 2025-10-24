# Nextbike Data Collection

Collect and store data from the Nextbike API every minute using a PostgreSQL database and a Python script.

## 🚀 Quick Demo Installation (For Validation Only)

```sh
# Clone repo
git clone https://github.com/zwoefler/nextbike-city-analysis.git
cd nextbike-city-analysis/data_collection

# Copy example environment file
cp .env.example .env

# Build and run the collection service
docker build -f CONTAINERFILE -t nextbike_collector:multiple_cities .
docker compose -f docker-compose.yaml up -d
```

## 📌 Production Setup

### 1. Install Dependencies
Ensure your system meets the following requirements:
- **IPv4 support** (GitHub & Nextbike do not support IPv6)
- **Docker & Docker Compose** installed


### 2. Set your city id
1. Find your city ID in [this document](../city_ids_2025_02_15.md). For Alternatives see end of [document]()

2. Copy and update environment variables:
   ```SHELL
   cp .env.example .env
   ```
3. Update the `.env` file with your city id:
   ```ini
   DB_TYPE=postgres
   DB_HOST=postgres
   DB_PORT=5432
   DB_NAME=nextbike_data
   DB_USER=bike_admin
   DB_PASSWORD=mybike
   CITY_IDS=467
   
   # Custom table names
   DB_CITIES_TABLE=public.cities
   DB_BIKES_TABLE=public.bikes
   DB_STATIONS_TABLE=public.stations
   ```

### 3. Build and start the collection service
```sh
docker build -f CONTAINERFILE -t nextbike_collector:multiple_cities .
docker compose -f docker-compose.yaml up -d
```

## 🔄 Updating the Collection Service
```sh
# Rebuild the image
docker build -f CONTAINERFILE -t nextbike_collector:multiple_cities .

# Restart the service without restarting dependencies
docker compose up -d --no-deps --build data_collector
```

## 📌 Generate City ID List
To find your city's Nextbike ID. 
Requires:
- jq
- curl

```sh
echo '|Country Code|City Name|Bikeshare Name|City ID|' > city_ids_$(date +%Y_%m_%d).md && \
echo '|----|----|----|---|' >> city_ids_$(date +%Y_%m_%d).md && \
curl -s https://api.nextbike.net/maps/nextbike-live.json | \
jq -r '.countries[] | select(.cities[0].uid) | "| \(.country) | \(.cities[0].name) | \(.name) | \(.cities[0].uid) |"' | sort >> city_ids_$(date +%Y_%m_%d).csv
```

## 📚 Sources
- [Nextbike API City IDs](https://github.com/ubahnverleih/WoBike/blob/master/Nextbike.md)
