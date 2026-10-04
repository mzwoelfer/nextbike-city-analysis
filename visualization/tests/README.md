# Visualization API Tests

## Run
- From `visualization/`: `python -m unittest discover -s tests -v`

## Test Without PostgreSQL
- `test_api.py` checks HTTP validation and timezone formatting.

## Test With PostgreSQL
- `test_api_integration.py` calls the real API and SQL against PostgreSQL.
- Set `DB_NAME=nextbike_api_test` and `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD` for a disposable database.
- Tests create required tables and seed then remove fixture rows. Never point them at the persistent application database.
- CI starts an isolated PostgreSQL service.
