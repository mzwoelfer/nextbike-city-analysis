import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import MagicMock, patch

# Stub StaticFiles before api.py is imported — /app/data doesn't exist locally
with patch("starlette.staticfiles.StaticFiles", MagicMock()):
    from api import app

from fastapi.testclient import TestClient

client = TestClient(app)


def _mock_conn(rows):
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)

    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    return conn


def _mock_conn_with_fetchone(fetchone_values, fetchall_rows):
    cursor = MagicMock()
    cursor.fetchone.side_effect = fetchone_values
    cursor.fetchall.return_value = fetchall_rows
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)

    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    return conn


class TestAvailableEndpoint(unittest.TestCase):

    @patch("api.get_connection")
    def test_response_includes_city_name(self, mock_get_conn):
        mock_get_conn.return_value = _mock_conn([
            (467, "Gießen", ["2026-06-08", "2026-06-07"]),
        ])
        data = client.get("/api/available").json()
        self.assertIn("city_name", data[0])

    @patch("api.get_connection")
    def test_city_name_is_never_null(self, mock_get_conn):
        mock_get_conn.return_value = _mock_conn([
            (467, "Gießen", ["2026-06-08"]),
            (999, "999",    ["2026-06-08"]),
        ])
        data = client.get("/api/available").json()
        for item in data:
            self.assertIsNotNone(item.get("city_name"),
                                 f"city_name is null for city_id={item.get('city_id')}")
            self.assertNotEqual(item["city_name"], "")

    @patch("api.get_connection")
    def test_city_id_and_dates_still_present(self, mock_get_conn):
        mock_get_conn.return_value = _mock_conn([
            (467, "Gießen", ["2026-06-08"]),
        ])
        item = client.get("/api/available").json()[0]
        self.assertIn("city_id", item)
        self.assertIn("dates", item)
        self.assertIsInstance(item["dates"], list)


class TestTimezoneAwareEndpoints(unittest.TestCase):

    @patch("api.get_connection")
    def test_trips_response_includes_timezone_and_offset_timestamp(self, mock_get_conn):
        start_time = datetime(2026, 6, 8, 10, 0, tzinfo=ZoneInfo("UTC"))
        end_time = datetime(2026, 6, 8, 10, 5, tzinfo=ZoneInfo("UTC"))

        mock_get_conn.return_value = _mock_conn([
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
        ])

        payload = client.get("/api/trips?city_id=467&date=2026-06-08").json()
        self.assertEqual(payload["timezone"], "Europe/Berlin")
        feature = payload["features"][0]
        self.assertEqual(feature["properties"]["timezone"], "Europe/Berlin")
        self.assertRegex(feature["properties"]["start_time"], r"[+-]\d{2}:\d{2}$")
        self.assertRegex(feature["properties"]["end_time"], r"[+-]\d{2}:\d{2}$")

    @patch("api.get_connection")
    def test_stations_response_includes_timezone_and_offset_minute(self, mock_get_conn):
        station_minute = datetime(2026, 6, 8, 12, 30)
        mock_get_conn.return_value = _mock_conn_with_fetchone(
            fetchone_values=[("Europe/Berlin",), (datetime(2026, 6, 8).date(),)],
            fetchall_rows=[
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
                )
            ],
        )

        payload = client.get("/api/stations?city_id=467&date=2026-06-08").json()
        self.assertEqual(payload[0]["timezone"], "Europe/Berlin")
        self.assertRegex(payload[0]["minute"], r"[+-]\d{2}:\d{2}$")


if __name__ == "__main__":
    unittest.main()