import os
import unittest
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

from api import app, get_connection


TEST_CITY_ID = 987654321
TEST_DATE = "2026-06-08"
TEST_TIMESTAMP = datetime(2026, 6, 8, 10, 30, tzinfo=timezone.utc)
ROUTE_START = (52.5, 13.4)
ROUTE_END = (52.51, 13.41)
ROUTE_COORDINATES = [[13.4, 52.5], [13.41, 52.51]]
TEST_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "collection"
    / "create_bike_and_stations_db.sql"
)


@unittest.skipUnless(
    os.getenv("DB_NAME") == "nextbike_api_test",
    "requires dedicated PostgreSQL database DB_NAME=nextbike_api_test",
)
class TestApiPostgresIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(TEST_SCHEMA_PATH.read_text())

    def setUp(self):
        self.clear_fixture()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO public.cities
                       (city_id, city_name, timezone, set_point_bikes,
                        available_bikes, last_updated)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (TEST_CITY_ID, "Test City", "Europe/Berlin", 10, 3, TEST_TIMESTAMP),
                )
                cursor.execute(
                    """INSERT INTO public.routes
                       (start_latitude, start_longitude, end_latitude,
                        end_longitude, distance_meters, coordinates)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (*ROUTE_START, *ROUTE_END, 1200.0, Jsonb(ROUTE_COORDINATES)),
                )
                route_id = cursor.fetchone()["id"]
                cursor.execute(
                    """INSERT INTO public.trips
                       (bike_number, city_id, start_time, end_time,
                        duration_seconds, route_id)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        "trip-bike",
                        TEST_CITY_ID,
                        TEST_TIMESTAMP,
                        datetime(2026, 6, 8, 10, 45, tzinfo=timezone.utc),
                        900.0,
                        route_id,
                    ),
                )
                cursor.execute(
                    """INSERT INTO public.stations
                       (uid, latitude, longitude, name, spot, station_number,
                        maintenance, terminal_type, last_updated, city_id, city_name)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        101,
                        52.5,
                        13.4,
                        "Test Station",
                        True,
                        101,
                        False,
                        "virtual",
                        TEST_TIMESTAMP,
                        TEST_CITY_ID,
                        "Test City",
                    ),
                )
                cursor.executemany(
                    """INSERT INTO public.bikes
                       (bike_number, latitude, longitude, bike_type,
                        station_number, last_updated, city_id, city_name)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    [
                        (
                            "station-bike-150",
                            52.5,
                            13.4,
                            "150",
                            101,
                            TEST_TIMESTAMP,
                            TEST_CITY_ID,
                            "Test City",
                        ),
                        (
                            "station-bike-237",
                            52.5,
                            13.4,
                            "237",
                            101,
                            TEST_TIMESTAMP,
                            TEST_CITY_ID,
                            "Test City",
                        ),
                        (
                            "loose-bike",
                            52.51,
                            13.41,
                            "237",
                            0,
                            TEST_TIMESTAMP,
                            TEST_CITY_ID,
                            "Test City",
                        ),
                    ],
                )

    def tearDown(self):
        self.clear_fixture()

    @staticmethod
    def clear_fixture():
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM public.trips WHERE city_id = %s", (TEST_CITY_ID,))
                cursor.execute("DELETE FROM public.bikes WHERE city_id = %s", (TEST_CITY_ID,))
                cursor.execute("DELETE FROM public.stations WHERE city_id = %s", (TEST_CITY_ID,))
                cursor.execute(
                    """DELETE FROM public.routes
                       WHERE start_latitude = %s AND start_longitude = %s
                         AND end_latitude = %s AND end_longitude = %s""",
                    (*ROUTE_START, *ROUTE_END),
                )
                cursor.execute("DELETE FROM public.cities WHERE city_id = %s", (TEST_CITY_ID,))

    def test_available_lists_seeded_city_and_date(self):
        response = TestClient(app).get("/api/available")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            {"city_id": str(TEST_CITY_ID), "city_name": "Test City", "dates": [TEST_DATE]},
            response.json(),
        )

    def test_trips_returns_seeded_trip_and_route(self):
        response = TestClient(app).get(
            f"/api/trips?city_id={TEST_CITY_ID}&date={TEST_DATE}"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["timezone"], "Europe/Berlin")
        self.assertEqual(len(payload["features"]), 1)
        trip = payload["features"][0]
        self.assertEqual(trip["properties"]["bike_number"], "trip-bike")
        self.assertEqual(trip["geometry"]["coordinates"], ROUTE_COORDINATES)

    def test_stations_returns_available_bike_and_type_counts(self):
        response = TestClient(app).get(
            f"/api/stations?city_id={TEST_CITY_ID}&date={TEST_DATE}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        station = response.json()[0]
        self.assertEqual(station["name"], "Test Station")
        self.assertEqual(station["bike_count"], 2)
        self.assertEqual(station["bike_type_counts"], {"150": 1, "237": 1})

    def test_bikes_returns_standalone_bike_observation(self):
        response = TestClient(app).get(
            f"/api/bikes?city_id={TEST_CITY_ID}&date={TEST_DATE}"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["timezone"], "Europe/Berlin")
        self.assertEqual(len(payload["bikes"]), 1)
        bike = payload["bikes"][0]
        self.assertEqual(bike["bike_number"], "loose-bike")
        self.assertEqual(bike["bike_type"], "237")