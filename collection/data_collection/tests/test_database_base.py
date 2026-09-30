import unittest
from datetime import datetime
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

    def test_database_client_constructs_backend_and_forwards_methods(self):
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
        config = SimpleNamespace(db_type=backend_name)
        client = DatabaseClient(config)
        city = object()
        bikes = [object()]
        stations = [object()]

        client.insert_city_information(city)
        client.insert_bike_entries(bikes)
        client.insert_station_entries(stations)

        self.assertIs(client.client.config, config)
        self.assertIs(client.client.inserted_city, city)
        self.assertIs(client.client.inserted_bikes, bikes)
        self.assertIs(client.client.inserted_stations, stations)


if __name__ == "__main__":
    unittest.main()