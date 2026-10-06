import unittest
from types import SimpleNamespace

from database.base import (
    AbstractDatabaseClient,
    DatabaseClient,
    get_backend,
    register_backend,
)


class TestDatabaseBackendRegistry(unittest.TestCase):
    def test_register_and_get_backend(self):
        class TestBackend(AbstractDatabaseClient):
            def insert_city_information(self, city):
                pass

            def insert_bike_entries(self, bike_entries):
                pass

            def insert_station_entries(self, station_entries):
                pass

        backend_name = f"test_backend_{id(self)}"
        register_backend(backend_name)(TestBackend)

        self.assertIs(get_backend(backend_name), TestBackend)

    def test_unknown_backend_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "Unknown database backend"):
            get_backend(f"missing_backend_{id(self)}")

    def setUp(self):
        class TestBackend(AbstractDatabaseClient):
            def __init__(self, config):
                self.config = config
                self.inserted_city = None
                self.inserted_bikes = None
                self.inserted_stations = None

            def insert_city_information(self, city):
                self.inserted_city = city

            def insert_bike_entries(self, bike_entries):
                self.inserted_bikes = bike_entries

            def insert_station_entries(self, station_entries):
                self.inserted_stations = station_entries

        backend_name = f"forwarding_backend_{id(self)}"
        register_backend(backend_name)(TestBackend)
        self.config = SimpleNamespace(db_type=backend_name)
        self.client = DatabaseClient(self.config)
        self.city = object()
        self.bikes = [object()]
        self.stations = [object()]

    def test_database_client_constructs_backend_with_config(self):
        self.assertIs(self.client.client.config, self.config)

    def test_database_client_forwards_city_information(self):
        self.client.insert_city_information(self.city)

        self.assertIs(self.client.client.inserted_city, self.city)

    def test_database_client_forwards_bike_entries(self):
        self.client.insert_bike_entries(self.bikes)

        self.assertIs(self.client.client.inserted_bikes, self.bikes)

    def test_database_client_forwards_station_entries(self):
        self.client.insert_station_entries(self.stations)

        self.assertIs(self.client.client.inserted_stations, self.stations)


if __name__ == "__main__":
    unittest.main()