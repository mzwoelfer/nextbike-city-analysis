import unittest

from nextbike_processing.cities import (
    CityRepository,
)


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.query = None
        self.parameters = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, parameters):
        self.query = query
        self.parameters = parameters

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.cursor_instance = FakeCursor(row)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.cursor_instance


class TestCityQueries(unittest.TestCase):
    def test_get_city_coordinates_returns_database_values(self):
        connection = FakeConnection((50.5, 8.6))
        repository = CityRepository(lambda: connection)

        result = repository.get_coordinates(467)

        self.assertEqual(result, (50.5, 8.6))
        self.assertIn("SELECT latitude, longitude", connection.cursor_instance.query)
        self.assertEqual(connection.cursor_instance.parameters, (467,))

    def test_get_city_timezone_returns_database_value(self):
        connection = FakeConnection(("Europe/Berlin",))
        repository = CityRepository(lambda: connection)

        self.assertEqual(repository.get_timezone(467), "Europe/Berlin")

    def test_get_city_timezone_defaults_to_utc_without_a_row(self):
        connection = FakeConnection(None)
        repository = CityRepository(lambda: connection)

        self.assertEqual(repository.get_timezone(467), "UTC")


if __name__ == "__main__":
    unittest.main()
