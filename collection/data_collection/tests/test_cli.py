import os
import runpy
import sys
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import query_nextbike
from query_nextbike import NextbikeCLI, AppConfig


class TestNextbikeCLI(unittest.TestCase):
    def test_single_city_id(self):
        cli = NextbikeCLI(["--city-ids", "467"])

        expected_ids = [467]
        self.assertEqual(cli.city_ids, expected_ids)

    def test_multiple_city_ids(self):
        cli = NextbikeCLI(["--city-id", "467", "123"])

        expected_ids = [467, 123]
        self.assertEqual(cli.city_ids, expected_ids)


class TestAppConfig(unittest.TestCase):
    def setUp(self) -> None:
        """Never start a test with set CITY_IDS!"""
        os.environ["CITY_IDS"] = ""

    def tearDown(self):
        """Always remove CITY_IDS after each test"""
        os.environ["CITY_IDS"] = ""

    def test_read_env_ids(self):
        os.environ["CITY_IDS"] = "100,200"
        config = AppConfig()

        expected_ids = [100, 200]
        self.assertEqual(config.city_ids, expected_ids)

    def test_cli_ids_take_precedence(self):
        os.environ["CITY_IDS"] = "100,200"
        cli_ids = [123, 456]
        config = AppConfig(cli_city_ids=cli_ids)

        self.assertEqual(config.city_ids, cli_ids)

    def test_cli_city_ids(self):
        cli_ids = [123, 456]
        config = AppConfig(cli_city_ids=cli_ids)

        self.assertEqual(config.city_ids, cli_ids)

    def test_no_city_ids_raises_error_message(self):
        os.environ["CITY_IDS"] = ""
        with self.assertRaises(ValueError):
            AppConfig(cli_city_ids=[])

    def test_no_city_ids_return_error_message(self):
        os.environ["CITY_IDS"] = ""
        with self.assertRaisesRegex(
            ValueError, "No city ID provided. Use --city-ids or set CITY_IDS in .env."
        ):
            AppConfig(cli_city_ids=[])


class TestMain(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 30, 12)
        self.city = SimpleNamespace(city_id=467, last_updated=self.now)
        self.bikes = [object()]
        self.stations = [object()]
        self.cli = SimpleNamespace(city_ids=[467], save=True)
        self.config = SimpleNamespace(
            city_ids=[467],
            stations_sync_interval_hours=24,
            cities_sync_interval_hours=720,
        )
        self.database = MagicMock()
        self.database.get_last_station_sync.return_value = None
        self.database.get_last_city_sync.return_value = None

    def run_main(self):
        with (
            patch("query_nextbike.NextbikeCLI", return_value=self.cli),
            patch("query_nextbike.AppConfig", return_value=self.config),
            patch("query_nextbike.DatabaseClient", return_value=self.database),
            patch("query_nextbike.NextbikeAPI"),
            patch(
                "query_nextbike.process_nextbike_data",
                return_value=(self.city, self.bikes, self.stations),
            ),
        ):
            query_nextbike.main()

    def test_no_save_skips_database_writes_and_sync_lookups(self):
        self.cli.save = False

        self.run_main()

        self.database.insert_bike_entries.assert_not_called()
        self.database.get_last_station_sync.assert_not_called()
        self.database.get_last_city_sync.assert_not_called()

    def test_first_save_inserts_bikes_stations_and_city(self):
        self.run_main()

        self.database.insert_bike_entries.assert_called_once_with(self.bikes)
        self.database.insert_station_entries.assert_called_once_with(self.stations)
        self.database.insert_city_information.assert_called_once_with(self.city)

    def test_sync_intervals_are_checked_independently(self):
        self.database.get_last_station_sync.return_value = self.now - timedelta(hours=25)
        self.database.get_last_city_sync.return_value = self.now - timedelta(hours=1)

        self.run_main()

        self.database.insert_station_entries.assert_called_once_with(self.stations)
        self.database.insert_city_information.assert_not_called()

    def test_city_sync_occurs_when_its_interval_expires(self):
        self.database.get_last_station_sync.return_value = self.now - timedelta(hours=1)
        self.database.get_last_city_sync.return_value = self.now - timedelta(hours=721)

        self.run_main()

        self.database.insert_station_entries.assert_not_called()
        self.database.insert_city_information.assert_called_once_with(self.city)

    def test_sync_is_skipped_when_intervals_have_not_expired(self):
        self.database.get_last_station_sync.return_value = self.now - timedelta(hours=1)
        self.database.get_last_city_sync.return_value = self.now - timedelta(hours=719)

        self.run_main()

        self.database.insert_station_entries.assert_not_called()
        self.database.insert_city_information.assert_not_called()


class TestScriptEntrypoint(unittest.TestCase):
    def test_help_invocation_reaches_cli_entrypoint_without_database_access(self):
        output = StringIO()

        with patch.object(sys, "argv", [query_nextbike.__file__, "--help"]):
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    runpy.run_path(query_nextbike.__file__, run_name="__main__")

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("--city-ids", output.getvalue())


if __name__ == "__main__":
    unittest.main()
