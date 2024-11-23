# Nextbike Data Aggregation Setup

Install the Nextbike data collection on a server using Containers.

Continuously collect and store data from the Nextbike API, every minute, ready for analysis.


## Prerequisites
Per entry roughly `0,12 KB`.

Make sure your system has at least the following resources:
> Note: IPv4 is required as GitHub and Nextbike do not support IPv6.

| Resource                | Minimal Requirement                              |
| ----------------------- | ------------------------------------------------ |
| Network                 | Support IPv4                                     |
| RAM                     | 1 GiB                                            |
| Disk                    | 25 GiB (@420 bikes - sufficient for a year)      |
| Docker                  | Container runtime installed                      |


## Install

```SHELL
# Clone rpeo
git clone https://github.com/zwoefler/nextbike-city-analysis.git
cd nextbike-city-analysis/data_collection

# Copy the fake env vars
cp data_collection.env.example data_collection.env

# Pulls & builds the images and starts the aggregation in the background
docker compose --file docker-compose.yaml up -d
```



