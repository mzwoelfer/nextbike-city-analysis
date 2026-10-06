# Visualization API Tests

## Run
- From `visualization/`: `python -m unittest discover -s tests -v`

## Test Without PostgreSQL
- `test_api.py` checks HTTP validation and timezone formatting.

## Test With PostgreSQL
- `test_api_integration.py` calls the real API and SQL against PostgreSQL.
- CI starts an empty, temporary `postgres:15` service; no database file is checked into the repository.
- From `visualization/`, build the test runner and run the suite with one command:

	```sh
	docker compose -f tests/docker-compose.yml run --build --rm tests
	```

- Compose initializes PostgreSQL from the canonical schema, requests health-based startup, and passes database settings to the test container. The runner also retries database connections for runtimes that ignore Compose health conditions. The repository is bind-mounted, so source edits are available immediately; rerun the command to run tests again. It does not watch files or rerun automatically on save.
- Tests load the canonical schema from `collection/create_bike_and_stations_db.sql`, then seed and remove fixture rows.
- Stop and remove the test database with `docker compose -f tests/docker-compose.yml down`.
- Never point integration tests at the persistent application database. Use `nerdctl` instead of `docker` when that is your container runtime.
