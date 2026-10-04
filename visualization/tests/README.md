# Visualization API Tests

## Run
- From `visualization/`: `python -m unittest discover -s tests -v`

## Test Without PostgreSQL
- `test_api.py` checks HTTP validation and timezone formatting.

## Test With PostgreSQL
- `test_api_integration.py` calls the real API and SQL against PostgreSQL.
- CI starts an empty, temporary `postgres:15` service; no database file is checked into the repository.
- From `visualization/`, start the local test database with one command:

	```sh
	docker compose -f tests/docker-compose.yml up -d
	```

- Run tests from `visualization/`:

	```sh
	DB_HOST=127.0.0.1 DB_PORT=55432 DB_NAME=nextbike_api_test \
		DB_USER=test DB_PASSWORD=test python -m unittest discover -s tests -v
	```

- Compose starts `postgres:15` with temporary storage and a readiness healthcheck. Wait until the service is healthy before running tests. Tests load the canonical schema from `collection/create_bike_and_stations_db.sql`, then seed and remove fixture rows.
- Stop the test database with `docker compose -f tests/docker-compose.yml down`.
- Never point integration tests at the persistent application database. Use `nerdctl` instead of `docker` when that is your container runtime.
