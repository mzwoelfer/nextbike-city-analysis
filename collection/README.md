# Nextbike Data Collection

Collects bike and station data from the Nextbike API every minute. Stores it in PostgreSQL.

- Runs as part of the root `docker compose` stack. 
- Standalone `docker-compose.yaml` for isolated testing.

## Database schema

The collection service writes to three tables:

| Table | Description |
|---|---|
| `public.cities` | City metadata (id, name, country) |
| `public.bikes` | One row per bike per poll |
| `public.stations` | One row per station per poll |

Two additional tables are created by the same init script and used by the processor:

| Table | Description |
|---|---|
| `public.routes` | Cached OSM routes between station pairs |
| `public.trips` | Extracted trips with route references |

The schema is initialised automatically on a fresh container via `create_bike_and_stations_db.sql`.

To apply the schema to an already-running database:
```sh
docker exec -i nextbike_postgres psql -U $DB_USER -d $DB_NAME < collection/create_bike_and_stations_db.sql
```

## Production setup

The collector is started automatically as part of the root stack:
```sh
# From the project root
docker compose up -d
```

See the root [README](../README.md) for the full `.env` variable reference.

## Standalone / demo setup

For testing the collector in isolation:
```sh
cd collection/
cp .env.example .env   # adjust values
docker compose -f docker-compose.yaml up -d
```

## Updating the collector image
```sh
docker compose up -d --no-deps --build collector
```

## Finding your city ID

Requires `curl` and `jq`:
```sh
echo '|Country Code|City Name|Bikeshare Name|City ID|' > city_ids_$(date +%Y_%m_%d).md && \
echo '|----|----|----|---|' >> city_ids_$(date +%Y_%m_%d).md && \
curl -s https://api.nextbike.net/maps/nextbike-live.json | \
jq -r '.countries[] | select(.cities[0].uid) | "| \(.country) | \(.cities[0].name) | \(.name) | \(.cities[0].uid) |"' | sort >> city_ids_$(date +%Y_%m_%d).md
```

A pre-generated list is available at [city_ids_2025_02_15.md](../city_ids_2025_02_15.md).

## Sources
- [Nextbike API City IDs](https://github.com/ubahnverleih/WoBike/blob/master/Nextbike.md)
