import datetime
import os
import unittest
import uuid
from dataclasses import asdict, replace
from types import SimpleNamespace

import psycopg
from psycopg.rows import dict_row

from database.postgres import PostgresClient
from query_nextbike import Bike, City, Station


class TestPostgresOperations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database_url = os.getenv("TEST_DATABASE_URL")
        if not cls.database_url:
            raise unittest.SkipTest(
                "Set TEST_DATABASE_URL to run PostgreSQL integration tests"
            )

    def setUp(self):
        connection_info = psycopg.conninfo.conninfo_to_dict(self.database_url)
        config = SimpleNamespace(
            db_host=connection_info.get("host", "localhost"),
            db_port=connection_info.get("port", "5432"),
            db_name=connection_info.get("dbname"),
            db_user=connection_info.get("user"),
            db_password=connection_info.get("password"),
            db_cities_table="public.cities",
            db_bikes_table="public.bikes",
            db_stations_table="public.stations",
        )
        self.client = PostgresClient(config)
        self.city_id = uuid.uuid4().int % (2**31 - 2) + 1
        self.bike_number = f"test-{uuid.uuid4().hex}"
        self.station_uid = self.city_id
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.city = City(
            self.city_id,
            "Integration Town",
            "UTC",
            10.0,
            20.0,
            5,
            2,
            self.timestamp,
        )
        self.bike = Bike(
            self.bike_number,
            10.1,
            20.1,
            True,
            "ok",
            "150",
            101,
            self.station_uid,
            self.timestamp,
            self.city_id,
            "Integration Town",
        )
        self.station = Station(
            self.station_uid,
            10.2,
            20.2,
            "Integration Station",
            True,
            101,
            False,
            "sign",
            self.timestamp,
            self.city_id,
            "Integration Town",
        )

    def tearDown(self):
        with psycopg.connect(self.database_url) as connection:
            connection.execute(
                "DELETE FROM public.bikes WHERE bike_number = %s",
                (self.bike_number,),
            )
            connection.execute(
                "DELETE FROM public.stations WHERE city_id = %s",
                (self.city_id,),
            )
            connection.execute(
                "DELETE FROM public.cities WHERE city_id = %s",
                (self.city_id,),
            )

    def fetch_row(self, query, value):
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            return connection.execute(query, (value,)).fetchone()

    def test_insert_city_persists_named_city_fields(self):
        self.client.insert_city_information(self.city)

        row = self.fetch_row(
            "SELECT city_id, city_name, timezone, latitude, longitude, "
            "set_point_bikes, available_bikes, last_updated "
            "FROM public.cities WHERE city_id = %s",
            self.city_id,
        )

        self.assertEqual(row, asdict(self.city))

    def test_insert_bikes_persists_named_bike_fields(self):
        self.client.insert_bike_entries([self.bike])

        row = self.fetch_row(
            "SELECT bike_number, latitude, longitude, active, state, bike_type, "
            "station_number, station_uid, last_updated, city_id, city_name "
            "FROM public.bikes WHERE bike_number = %s",
            self.bike_number,
        )

        self.assertEqual(row, asdict(self.bike))

    def test_insert_stations_persists_named_station_fields(self):
        self.client.insert_station_entries([self.station])

        row = self.fetch_row(
            "SELECT uid, latitude, longitude, name, spot, station_number, maintenance, "
            "terminal_type, last_updated, city_id, city_name "
            "FROM public.stations WHERE uid = %s",
            self.station_uid,
        )

        self.assertEqual(row, asdict(self.station))

    def test_station_sync_returns_latest_persisted_timestamp(self):
        earlier_station = replace(
            self.station,
            uid=self.station_uid + 1,
            last_updated=self.timestamp - datetime.timedelta(hours=1),
        )
        self.client.insert_station_entries([earlier_station, self.station])

        self.assertEqual(self.client.get_last_station_sync(self.city_id), self.timestamp)

    def test_city_sync_returns_persisted_timestamp(self):
        self.client.insert_city_information(self.city)

        self.assertEqual(self.client.get_last_city_sync(self.city_id), self.timestamp)

    def test_station_sync_returns_none_when_city_has_no_stations(self):
        self.assertIsNone(self.client.get_last_station_sync(self.city_id))

    def test_city_sync_returns_none_when_city_is_missing(self):
        self.assertIsNone(self.client.get_last_city_sync(self.city_id))


if __name__ == "__main__":
    unittest.main()