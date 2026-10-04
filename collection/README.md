# Nextbike Data Collection

Collects bike and station data from the Nextbike API every minute and stores it in PostgreSQL.

- Runs as part of the root `docker compose` stack.
- Standalone `docker-compose.yaml` for isolated testing.

See the [project README](../README.md) for the root stack quick start and configuration.

## Database schema

The collection service writes to three tables:

| Table | Description |
|---|---|
| `public.cities` | City ID, name, timezone, location, and bike counts |
| `public.bikes` | One row per bike per poll |
| `public.stations` | One row per station per poll |

Two additional tables are created by the same init script and used by the processor:

| Table | Description |
|---|---|
| `public.routes` | Cached OSM routes between station pairs |
| `public.trips` | Extracted trips with route references |

Both Compose files mount [`create_bike_and_stations_db.sql`](create_bike_and_stations_db.sql) into PostgreSQL's initialization directory. PostgreSQL runs it when creating a database in an empty data volume.

From the repository root, create missing tables in an already-running database (existing tables are unchanged):
```sh
docker exec -i nextbike_postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < collection/create_bike_and_stations_db.sql
```

## Standalone / demo setup

For testing the collector in isolation:
```sh
cd collection/
cp .env.example .env   # adjust values
docker build -f CONTAINERFILE -t nextbike_collector:multiple_cities .
docker compose -f docker-compose.yaml up -d
```

## Updating the collector image
From the repository root:
```sh
docker compose up -d --no-deps --build collector
```

## Finding your city ID

From the repository root; requires `curl` and `jq`:
```sh
echo '|Country Code|City Name|Bikeshare Name|City ID|' > city_ids_$(date +%Y_%m_%d).md && \
echo '|----|----|----|---|' >> city_ids_$(date +%Y_%m_%d).md && \
curl -s https://api.nextbike.net/maps/nextbike-live.json | \
jq -r '.countries[] as $provider | $provider.cities[]? | select(.uid | type == "number") | "| \($provider.country) | \(.name) | \($provider.name) | \(.uid) |"' | sort >> city_ids_$(date +%Y_%m_%d).md
```

A pre-generated list is available at [city_ids_2026_10_04.md](../city_ids_2026_10_04.md).

## Sources
- [Nextbike API City IDs](https://github.com/ubahnverleih/WoBike/blob/master/Nextbike.md)
