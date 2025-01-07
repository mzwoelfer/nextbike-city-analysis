# Nextbike Data collection setup

Continuously collect and store data from the Nextbike API, every minute, ready for analysis.

> Run the collection setup locally (for testing purposes).
For production, run on a dedicated server (only tested with Debian12).
[Server requirements](#server-requirements) are listed below.

Uses Postgres as a database, and a Python3 script to pull the data.

## Install

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




