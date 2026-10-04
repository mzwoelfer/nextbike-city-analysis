# Visualization API Tests

## Run
- From `visualization/`: `python -m unittest discover -s tests -v`

## Test Without PostgreSQL
- `test_api.py` checks HTTP validation and timezone formatting.

## Test With PostgreSQL
- `test_api_integration.py` calls the real API and SQL against PostgreSQL.
- CI starts an empty, temporary `postgres:15` service; no database file is checked into the repository.
- Locally, start a temporary database container (no volume):

	```sh
	docker run -d --name nextbike-api-test-db \
		-e POSTGRES_DB=nextbike_api_test \
		-e POSTGRES_USER=test \
		-e POSTGRES_PASSWORD=test \
		-p 55432:5432 postgres:15
	```

- Wait for PostgreSQL, then run from `visualization/`:

	```sh
	docker exec nextbike-api-test-db pg_isready -U test -d nextbike_api_test
	DB_HOST=127.0.0.1 DB_PORT=55432 DB_NAME=nextbike_api_test \
		DB_USER=test DB_PASSWORD=test python -m unittest discover -s tests -v
	```

- Tests create required tables and seed then remove fixture rows. Remove the temporary database with `docker rm -f nextbike-api-test-db`.
- Never point integration tests at the persistent application database. Use `nerdctl` instead of `docker` when that is your container runtime.
