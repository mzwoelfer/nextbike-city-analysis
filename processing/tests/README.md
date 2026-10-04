# Processing Tests

## Run

From `processing/`, run the suite in containers:

```sh
docker compose -f tests/docker-compose.yml run --build --rm tests
```

- Compose starts an isolated PostgreSQL 15 database named `nextbike_processing_test`,
- initialized from `collection/create_bike_and_stations_db.sql`.

Most tests are unit tests with mocked external boundaries. `test_database_integration.py` checks route-cache queries and trip persistence against real PostgreSQL. Source files are bind-mounted; rerun the command after edits. Tests do not rerun automatically on save.

Remove remaining test services with:

```sh
docker compose -f tests/docker-compose.yml down
```
