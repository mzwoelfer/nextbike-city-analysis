import os
import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from fastapi.testclient import TestClient

# Stub StaticFiles before api.py is imported — /app/data doesn't exist locally
with patch("starlette.staticfiles.StaticFiles", MagicMock()):
    from api import app, bikes, get_connection, stations, trips

client = TestClient(app)


class RowCursor:
    def __init__(self, rows, fetchone_values=()):
        self.rows = rows
        self.fetchone_values = iter(fetchone_values)

    def execute(self, query, params=None):
        pass

    def fetchone(self):
        return next(self.fetchone_values)

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        return False


class RowConnection:
    def __init__(self, rows, fetchone_values=()):
        self.row_cursor = RowCursor(rows, fetchone_values)

    def cursor(self):
        return self.row_cursor

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        return False


@contextmanager
def database_with_results(rows, fetchone_values=()):
    connection = RowConnection(rows, fetchone_values)
    with patch("api.get_connection", return_value=connection):
        yield


class TestAvailableEndpoint(unittest.TestCase):

    def test_response_includes_city_name(self):
        with database_with_results([
            (467, "Gießen", ["2026-06-08", "2026-06-07"]),
        ]):
            data = client.get("/api/available").json()

        self.assertIn("city_name", data[0])

    def test_city_name_is_never_null(self):
        with database_with_results([
            (467, "Gießen", ["2026-06-08"]),
            (999, "999",    ["2026-06-08"]),
        ]):
            data = client.get("/api/available").json()

        for item in data:
            self.assertIsNotNone(item.get("city_name"),
                                 f"city_name is null for city_id={item.get('city_id')}")
            self.assertNotEqual(item["city_name"], "")

    def test_city_id_and_dates_still_present(self):
        with database_with_results([
            (467, "Gießen", ["2026-06-08"]),
        ]):
            item = client.get("/api/available").json()[0]

        self.assertIn("city_id", item)
        self.assertIn("dates", item)
        self.assertIsInstance(item["dates"], list)


class TestTimezoneAwareEndpoints(unittest.TestCase):

    def test_trips_rejects_empty_date_with_http_400(self):
        with self.assertRaises(HTTPException) as error:
            trips(city_id=467, date="")

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "date parameter is required")

    def test_stations_rejects_empty_date_with_http_400(self):
        with self.assertRaises(HTTPException) as error:
            stations(city_id=467, date="")

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "date parameter is required")

    def test_trips_response_includes_timezone_and_offset_timestamp(self):
        start_time = datetime(2026, 6, 8, 10, 0, tzinfo=ZoneInfo("UTC"))
        end_time = datetime(2026, 6, 8, 10, 5, tzinfo=ZoneInfo("UTC"))

        with database_with_results([
            (
                "42",
                start_time,
                end_time,
                300.0,
                1200.0,
                [[13.4, 52.5], [13.41, 52.51]],
                1,
                "Europe/Berlin",
            )
        ]):
            payload = client.get("/api/trips?city_id=467&date=2026-06-08").json()

        self.assertEqual(payload["timezone"], "Europe/Berlin")
        feature = payload["features"][0]
        self.assertEqual(feature["properties"]["timezone"], "Europe/Berlin")
        self.assertRegex(feature["properties"]["start_time"], r"[+-]\d{2}:\d{2}$")
        self.assertRegex(feature["properties"]["end_time"], r"[+-]\d{2}:\d{2}$")

    def test_stations_response_includes_timezone_and_offset_minute(self):
        station_minute = datetime(2026, 6, 8, 12, 30)
        with database_with_results(
            rows=[
                (
                    station_minute,
                    1,
                    99,
                    52.5,
                    13.4,
                    "Station",
                    True,
                    101,
                    False,
                    "virtual",
                    467,
                    "Gießen",
                    3,
                    "42, 43, 44",
                    {"150": 2, "237": 1},
                )
            ],
            fetchone_values=[("Europe/Berlin",), (datetime(2026, 6, 8).date(),)],
        ):
            payload = client.get("/api/stations?city_id=467&date=2026-06-08").json()

        self.assertEqual(payload[0]["timezone"], "Europe/Berlin")
        self.assertRegex(payload[0]["minute"], r"[+-]\d{2}:\d{2}$")
        self.assertEqual(payload[0]["bike_type_counts"], {"150": 2, "237": 1})


class TestBikesEndpoint(unittest.TestCase):

    def test_bikes_rejects_empty_date_with_http_400(self):
        with self.assertRaises(HTTPException) as error:
            bikes(city_id=467, date="")

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "date parameter is required")

    def test_response_includes_unassigned_bike_timeline(self):
        minute = datetime(2026, 6, 8, 12, 30)
        with database_with_results([
            ("42", 52.5, 13.4, 0, "237", minute, "Europe/Berlin"),
        ]):
            payload = client.get("/api/bikes?city_id=467&date=2026-06-08").json()

        self.assertEqual(payload["timezone"], "Europe/Berlin")
        self.assertEqual(len(payload["bikes"]), 1)
        bike = payload["bikes"][0]
        self.assertEqual(bike["bike_number"], "42")
        self.assertEqual(bike["bike_type"], "237")
        self.assertEqual(bike["station_number"], 0)
        self.assertRegex(bike["minute"], r"[+-]\d{2}:\d{2}$")


class TestDatabaseConnection(unittest.TestCase):

    @patch("api.psycopg.connect")
    def test_connection_uses_database_environment(self, connect):
        settings = {
            "DB_HOST": "db.test",
            "DB_PORT": "5432",
            "DB_NAME": "nextbike_test",
            "DB_USER": "tester",
            "DB_PASSWORD": "secret",
        }
        with patch.dict(os.environ, settings):
            get_connection()

        connect.assert_called_once_with(
            host=settings["DB_HOST"],
            port=settings["DB_PORT"],
            dbname=settings["DB_NAME"],
            user=settings["DB_USER"],
            password=settings["DB_PASSWORD"],
        )


if __name__ == "__main__":
    unittest.main()