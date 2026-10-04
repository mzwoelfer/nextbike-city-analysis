import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api import app, to_city_iso


client = TestClient(app)


class TestRequestValidation(unittest.TestCase):

    def test_trips_rejects_empty_date_with_http_400(self):
        response = client.get("/api/trips?city_id=467&date=")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "date parameter is required")

    def test_stations_rejects_empty_date_with_http_400(self):
        response = client.get("/api/stations?city_id=467&date=")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "date parameter is required")

    def test_bikes_rejects_empty_date_with_http_400(self):
        response = client.get("/api/bikes?city_id=467&date=")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "date parameter is required")


class TestTimezoneFormatting(unittest.TestCase):

    def test_utc_timestamp_formats_with_city_offset(self):
        timestamp = datetime(2026, 6, 8, 10, 0, tzinfo=timezone.utc)

        formatted = to_city_iso(timestamp, "Europe/Berlin")

        self.assertEqual(formatted, "2026-06-08T12:00:00+02:00")


if __name__ == "__main__":
    unittest.main()
