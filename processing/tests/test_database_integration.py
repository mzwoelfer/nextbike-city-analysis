import os
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from nextbike_processing import database
from nextbike_processing.stations import fetch_station_data


TEST_CITY_ID = 987654321
ROUTE_START = (52.5, 13.4)
ROUTE_END = (52.51, 13.41)
ROUTE_SEGMENTS = [[52.5, 13.4], [52.51, 13.41]]
TEST_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "collection"
    / "create_bike_and_stations_db.sql"
)


@unittest.skipUnless(
    os.getenv("DB_NAME") == "nextbike_processing_test",
    "requires dedicated PostgreSQL database DB_NAME=nextbike_processing_test",
)
class TestProcessingDatabaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with database.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(TEST_SCHEMA_PATH.read_text())

    def setUp(self):
        self.clear_fixture()

    def tearDown(self):
        self.clear_fixture()

    @staticmethod
    def clear_fixture():
        with database.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM public.trips WHERE city_id = %s",
                    (TEST_CITY_ID,),
                )
                cursor.execute(
                    "DELETE FROM public.bikes WHERE city_id = %s",
                    (TEST_CITY_ID,),
                )
                cursor.execute(
                    "DELETE FROM public.stations WHERE city_id = %s",
                    (TEST_CITY_ID,),
                )
                cursor.execute(
                    """DELETE FROM public.routes
                       WHERE start_latitude = %s AND start_longitude = %s
                         AND end_latitude = %s AND end_longitude = %s""",
                    (*ROUTE_START, *ROUTE_END),
                )
                cursor.execute(
                    "DELETE FROM public.cities WHERE city_id = %s",
                    (TEST_CITY_ID,),
                )

    @staticmethod
    def route_pairs():
        return pd.DataFrame(
            [(*ROUTE_START, *ROUTE_END)],
            columns=[
                "start_latitude",
                "start_longitude",
                "end_latitude",
                "end_longitude",
            ],
        )

    @staticmethod
    def route_data():
        return pd.DataFrame(
            [{
                "start_latitude": ROUTE_START[0],
                "start_longitude": ROUTE_START[1],
                "end_latitude": ROUTE_END[0],
                "end_longitude": ROUTE_END[1],
                "distance": 1200.0,
                "segments": ROUTE_SEGMENTS,
            }]
        )

    def test_uncached_route_pairs_excludes_route_already_in_database(self):
        with database.get_connection() as connection:
            database.insert_new_routes(self.route_data(), connection)
        requested = pd.concat(
            [
                self.route_pairs(),
                pd.DataFrame(
                    [(53.0, 14.0, 53.01, 14.01)],
                    columns=self.route_pairs().columns,
                ),
            ],
            ignore_index=True,
        )

        with database.get_connection() as connection:
            uncached = database.get_uncached_route_pairs(requested, connection)

        self.assertEqual(
            uncached.values.tolist(),
            [[53.0, 14.0, 53.01, 14.01]],
        )

    def test_route_cache_round_trip_preserves_coordinates_and_ignores_duplicate(self):
        route_data = self.route_data()

        with database.get_connection() as connection:
            database.insert_new_routes(route_data, connection)
            database.insert_new_routes(route_data, connection)
            cached = database.get_cached_routes(self.route_pairs(), connection)
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT count(*) FROM public.routes
                       WHERE start_latitude = %s AND start_longitude = %s
                         AND end_latitude = %s AND end_longitude = %s""",
                    (*ROUTE_START, *ROUTE_END),
                )
                route_count = cursor.fetchone()[0]

        self.assertEqual(route_count, 1)
        self.assertEqual(cached.iloc[0]["distance"], 1200.0)
        self.assertEqual(cached.iloc[0]["segments"], ROUTE_SEGMENTS)

    def test_insert_trips_links_cached_route_and_ignores_duplicate(self):
        with database.get_connection() as connection:
            database.insert_new_routes(self.route_data(), connection)
            trips = pd.DataFrame(
                [{
                    "bike_number": "processing-integration-bike",
                    "start_time": datetime(2026, 6, 8, 10, 0, tzinfo=timezone.utc),
                    "end_time": datetime(2026, 6, 8, 10, 5, tzinfo=timezone.utc),
                    "duration": 300.0,
                    "start_latitude": ROUTE_START[0],
                    "start_longitude": ROUTE_START[1],
                    "end_latitude": ROUTE_END[0],
                    "end_longitude": ROUTE_END[1],
                }]
            )
            database.insert_trips(trips, TEST_CITY_ID, connection)
            database.insert_trips(trips, TEST_CITY_ID, connection)
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT count(*), min(trips.route_id), min(routes.id)
                       FROM public.trips AS trips
                       LEFT JOIN public.routes AS routes ON routes.id = trips.route_id
                       WHERE trips.city_id = %s AND trips.bike_number = %s""",
                    (TEST_CITY_ID, "processing-integration-bike"),
                )
                trip_count, route_id, joined_route_id = cursor.fetchone()

        self.assertEqual(trip_count, 1)
        self.assertIsNotNone(route_id)
        self.assertEqual(route_id, joined_route_id)

    def test_fetch_station_data_aggregates_bikes_and_types(self):
        observation_time = datetime(2026, 6, 8, 10, 30, tzinfo=timezone.utc)
        with database.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO public.cities
                       (city_id, city_name, timezone, set_point_bikes,
                        available_bikes, last_updated)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        TEST_CITY_ID,
                        "Processing Test City",
                        "Europe/Berlin",
                        10,
                        2,
                        observation_time,
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
                        "Processing Test Station",
                        True,
                        101,
                        False,
                        "virtual",
                        observation_time,
                        TEST_CITY_ID,
                        "Processing Test City",
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
                            observation_time,
                            TEST_CITY_ID,
                            "Processing Test City",
                        ),
                        (
                            "station-bike-237",
                            52.5,
                            13.4,
                            "237",
                            101,
                            observation_time,
                            TEST_CITY_ID,
                            "Processing Test City",
                        ),
                    ],
                )

        stations = fetch_station_data(TEST_CITY_ID, "2026-06-08")

        self.assertEqual(len(stations), 1)
        station = stations.iloc[0]
        self.assertEqual(station["name"], "Processing Test Station")
        self.assertEqual(station["bike_count"], 2)
        self.assertEqual(
            set(station["bike_list"].split(", ")),
            {"station-bike-150", "station-bike-237"},
        )
        self.assertEqual(
            dict(item.split("=") for item in station["bike_type_counts"].split(";")),
            {"150": "1", "237": "1"},
        )
        self.assertEqual(station["minute"], "2026-06-08T12:30:00+02:00")


if __name__ == "__main__":
    unittest.main()