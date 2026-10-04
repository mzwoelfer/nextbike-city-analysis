import re
import unittest
import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from database.postgres import PostgresClient
from query_nextbike import City, Bike, Station


class TestCityInsertSQL(unittest.TestCase):
    def setUp(self):
        self.table_name = "cities"
        self.sql_statement = PostgresClient.city_sql_insert_statement(self.table_name)

        now = datetime.datetime.now()
        self.city = City(
            city_id=1,
            city_name="TestTown",
            timezone="UTC",
            latitude=10.0,
            longitude=20.0,
            set_point_bikes=5,
            available_bikes=2,
            last_updated=now,
        )

    def test_all_city_dicts_keys_present_in_sql(self):
        for city_key in self.city.__dict__.keys():
            self.assertIn(f"%({city_key})s", self.sql_statement)

    def test_no_unknown_placeholders(self):
        placeholders = re.findall(r"%\((.*?)\)s", self.sql_statement)
        for placeholder in placeholders:
            self.assertIn(placeholder, self.city.__dict__)


class TestBikesInsertStatement(unittest.TestCase):
    def setUp(self):
        self.table_name = "bikes"
        self.sql_statement = PostgresClient.bike_sql_insert_statement(self.table_name)

        now = datetime.datetime.now()
        self.bike = Bike(
            bike_number="12345",
            latitude=47.1,
            longitude=11.2,
            active=True,
            state="ok",
            bike_type="150",
            station_number=999,
            station_uid=555,
            last_updated=now,
            city_id=773,
            city_name="Kufstein",
        )

    def test_bike_keys_Present_in_sql_statement(self):
        for bike_key in self.bike.__dict__.keys():
            self.assertIn(f"%({bike_key})s", self.sql_statement)

    def test_no_unknown_placeholders(self):
        placeholders = re.findall(r"%\((.*?)\)s", self.sql_statement)
        for placeholder in placeholders:
            self.assertIn(placeholder, self.bike.__dict__)


class TestStationInsertStatement(unittest.TestCase):
    def setUp(self):
        self.table_name = "stations"
        self.sql_statement = PostgresClient.station_sql_insert_statement(
            self.table_name
        )

        self.now = datetime.datetime.now()
        self.station = Station(
            uid=1001,
            latitude=47.1,
            longitude=11.2,
            name="Bahnhof",
            spot=True,
            station_number=12345,
            maintenance=False,
            terminal_type="sign",
            last_updated=self.now,
            city_id=773,
            city_name="Kufstein",
        )

    def test_bike_keys_Present_in_sql_statement(self):
        for station_key in self.station.__dict__.keys():
            self.assertIn(f"%({station_key})s", self.sql_statement)

    def test_no_unknown_placeholders(self):
        placeholders = re.findall(r"%\((.*?)\)s", self.sql_statement)
        for placeholder in placeholders:
            self.assertIn(placeholder, self.station.__dict__)


class TestPostgresOperations(unittest.TestCase):
    def setUp(self):
        config = SimpleNamespace(
            db_host="localhost",
            db_port="5432",
            db_name="test",
            db_user="test",
            db_password="test",
            db_cities_table="public.cities",
            db_bikes_table="public.bikes",
            db_stations_table="public.stations",
        )
        self.client = PostgresClient(config)
        self.connection = MagicMock()
        self.connection.__enter__.return_value = self.connection
        self.cursor = MagicMock()
        self.connection.cursor.return_value.__enter__.return_value = self.cursor

    @patch("database.postgres.psycopg.connect")
    def test_insert_city_executes_parameters_and_commits(self, mock_connect):
        mock_connect.return_value = self.connection
        city = City(1, "Town", "UTC", 1.0, 2.0, 3, 2, datetime.datetime.now())

        self.client.insert_city_information(city)

        self.cursor.execute.assert_called_once_with(
            PostgresClient.city_sql_insert_statement("public.cities"), city.__dict__
        )
        self.connection.commit.assert_called_once_with()

    @patch("database.postgres.psycopg.connect")
    def test_insert_bikes_bulk_executes_parameters_and_commits(self, mock_connect):
        mock_connect.return_value = self.connection
        bikes = [
            Bike("42", 1.0, 2.0, True, "ok", "bike", 3, 4, datetime.datetime.now(), 5, "Town"),
            Bike("43", 1.1, 2.1, True, "ok", "bike", 6, 7, datetime.datetime.now(), 5, "Town"),
        ]

        self.client.insert_bike_entries(bikes)

        self.cursor.executemany.assert_called_once_with(
            PostgresClient.bike_sql_insert_statement("public.bikes"),
            [bike.__dict__ for bike in bikes],
        )
        self.connection.commit.assert_called_once_with()

    @patch("database.postgres.psycopg.connect")
    def test_insert_stations_bulk_executes_parameters_and_commits(self, mock_connect):
        mock_connect.return_value = self.connection
        stations = [
            Station(1, 1.0, 2.0, "Station", True, 3, False, "terminal", datetime.datetime.now(), 5, "Town")
        ]

        self.client.insert_station_entries(stations)

        self.cursor.executemany.assert_called_once_with(
            PostgresClient.station_sql_insert_statement("public.stations"),
            [station.__dict__ for station in stations],
        )
        self.connection.commit.assert_called_once_with()

    def test_sync_lookups_return_timestamp_or_none(self):
        timestamp = datetime.datetime(2026, 9, 30)
        cases = (
            ("get_last_station_sync", timestamp),
            ("get_last_city_sync", timestamp),
        )

        for method_name, result in cases:
            with self.subTest(method=method_name, result=result):
                with patch("database.postgres.psycopg.connect", return_value=self.connection):
                    self.cursor.fetchone.return_value = (result,)
                    self.assertEqual(getattr(self.client, method_name)(467), timestamp)

                with patch("database.postgres.psycopg.connect", return_value=self.connection):
                    self.cursor.fetchone.return_value = (None,)
                    self.assertIsNone(getattr(self.client, method_name)(467))

                with patch("database.postgres.psycopg.connect", return_value=self.connection):
                    self.cursor.fetchone.return_value = None
                    self.assertIsNone(getattr(self.client, method_name)(467))
