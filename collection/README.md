# Nextbike Data collection setup

Continuously collect and store data from the Nextbike API, every minute, ready for analysis.

> Run the collection setup locally (for testing purposes).
For production, run on a dedicated server (only tested with Debian12).
[Server requirements](#server-requirements) are listed below.

Uses Postgres as a database, and a Python3 script to pull the data.

## How to collect data from my city?
Find your city ID in [this document](../city_ids_2025_02_15.md).

Alternatively:
Find your city_id in this output from the Nextbike API:
```SHELL
curl https://api.nextbike.net/maps/nextbike-live.json | jq '.countries[] | "|\(.country)|\(.cities[0].name)|\(.name)|\(.cities[0].uid)|"' | tr -d '"' | grep -v null | sort | less
```

## Demo Install

```SHELL
# Clone rpeo
git clone https://github.com/zwoefler/nextbike-city-analysis.git
cd nextbike-city-analysis/data_collection

# Copy the fake env vars
cp .env.example .env

docker build --file CONTAINERFILE -t nextbike_collector:multiple_cities .

# Pulls & builds the images and starts the collection in the background
docker compose --file docker-compose.yaml up -d
```


## Update to new collection version
Build the collection image:
```SHELL
docker build --file CONTAINERFILE -t nextbike_collector:multiple_cities .
```

Restart the service: Restarting the `data_collector` service to use the latest changes:
```SHELL
docker compose up -d --no-deps --build data_collector
```

- `-d` starts the service detached (in the background)
- `--no-deps` prevents restarting dependencies (the database)
- `--build` ensures the updated image is used 


## Server requirements

Make sure your system has at least the following resources:
> Note: Your server requires IPv4.
> GitHub and Nextbike do not support IPv6!

| Resource                | Minimal Requirement                              |
| ----------------------- | ------------------------------------------------ |
| Network                 | Support IPv4                                     |
| RAM                     | 1 GiB                                            |
| Disk                    | 25 GiB (per 500 bikes, good for ~6 months)       |
| Docker                  | Container runtime installed                      |


## How does it work?
🚧 TBD

## Useful stuff
Create the city_ids list markdown file.
Pulls the latest Nextbike API JSON endpoint.
Requires:
- jq
- curl
```SHELL
echo '|Country Code|City Name|Bikeshare Name|City ID|' > city_ids_$(date +%Y_%m_%d).md && echo '|----|----|----|---|' >> city_ids_$(date +%Y_%m_%d).md && curl -s https://api.nextbike.net/maps/nextbike-live.json | jq -r '.countries[] | select(.cities[0].uid) | "| \(.country) | \(.cities[0].name) | \(.name) | \(.cities[0].uid) |"' | sort >> city_ids_$(date +%Y_%m_%d).md
```

## 📚 Sources
[Find city ID from Nextbike API](https://github.com/ubahnverleih/WoBike/blob/master/Nextbike.md). 
