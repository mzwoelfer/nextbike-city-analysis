import json
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from nextbike_processing import database


PAIR_COLUMNS = [
    "start_latitude",
    "start_longitude",
    "end_latitude",
    "end_longitude",
]


class TestDatabaseRouteCache(unittest.TestCase):
    def setUp(self):
        self.cursor = MagicMock()
        cursor_context = MagicMock()
        cursor_context.__enter__.return_value = self.cursor
        cursor_context.__exit__.return_value = False
        self.connection = MagicMock()
        self.connection.cursor.return_value = cursor_context
        self.pairs = pd.DataFrame([[1, 2, 3, 4]], columns=PAIR_COLUMNS)

    def test_uncached_pairs_returns_copy_for_empty_input(self):
        pairs = pd.DataFrame(columns=PAIR_COLUMNS)

        result = database.get_uncached_route_pairs(pairs, self.connection)

        pd.testing.assert_frame_equal(result, pairs)
        self.assertIsNot(result, pairs)
        self.connection.cursor.assert_not_called()

    def test_uncached_pairs_returns_empty_frame_when_all_routes_are_cached(self):
        self.cursor.fetchall.return_value = []

        result = database.get_uncached_route_pairs(self.pairs, self.connection)

        self.assertEqual(result.columns.tolist(), PAIR_COLUMNS)
        self.assertTrue(result.empty)
        self.assertEqual(self.cursor.execute.call_args.args[1], [1.0, 2.0, 3.0, 4.0])

    def test_uncached_pairs_returns_database_rows(self):
        self.cursor.fetchall.return_value = [(1.0, 2.0, 3.0, 4.0)]

        result = database.get_uncached_route_pairs(self.pairs, self.connection)

        self.assertEqual(result.iloc[0].tolist(), [1.0, 2.0, 3.0, 4.0])

    def test_cached_routes_handles_empty_input_and_no_matches(self):
        result = database.get_cached_routes(pd.DataFrame(columns=PAIR_COLUMNS), self.connection)
        self.assertTrue(result.empty)
        self.cursor.execute.assert_not_called()

        self.cursor.fetchall.return_value = []
        result = database.get_cached_routes(self.pairs, self.connection)
        self.assertTrue(result.empty)

    def test_cached_routes_converts_geojson_coordinates_to_lat_lon(self):
        self.cursor.fetchall.return_value = [(1, 2, 3, 4, 500, [[20, 10], [40, 30]])]

        result = database.get_cached_routes(self.pairs, self.connection)

        self.assertEqual(result.columns.tolist(), PAIR_COLUMNS + ["distance", "segments"])
        self.assertEqual(result.iloc[0]["distance"], 500)
        self.assertEqual(result.iloc[0]["segments"], [[10, 20], [30, 40]])


class TestDatabaseWrites(unittest.TestCase):
    def setUp(self):
        self.cursor = MagicMock()
        cursor_context = MagicMock()
        cursor_context.__enter__.return_value = self.cursor
        cursor_context.__exit__.return_value = False
        self.connection = MagicMock()
        self.connection.cursor.return_value = cursor_context

    def test_insert_new_routes_skips_empty_segments_and_converts_coordinates(self):
        routes = pd.DataFrame(
            [
                {"start_latitude": 1, "start_longitude": 2, "end_latitude": 3, "end_longitude": 4, "distance": 5, "segments": []},
                {"start_latitude": 1, "start_longitude": 2, "end_latitude": 3, "end_longitude": 4, "distance": 5, "segments": [[10, 20], [30, 40]]},
            ]
        )

        inserted = database.insert_new_routes(routes, self.connection)

        self.assertEqual(inserted, 1)
        self.assertEqual(self.cursor.execute.call_count, 1)
        params = self.cursor.execute.call_args.args[1]
        self.assertEqual(params[-1], json.dumps([[20, 10], [40, 30]]))
        self.connection.commit.assert_called_once_with()

    def test_insert_trips_returns_zero_for_empty_frame(self):
        result = database.insert_trips(pd.DataFrame(), 467, self.connection)

        self.assertEqual(result, 0)
        self.connection.cursor.assert_not_called()
        self.connection.commit.assert_not_called()

    def test_insert_trips_writes_records_and_commits(self):
        trips = pd.DataFrame(
            [{
                "bike_number": "42",
                "start_time": "2026-06-08T10:00:00",
                "end_time": "2026-06-08T10:05:00",
                "duration": 300,
                "start_latitude": 1,
                "start_longitude": 2,
                "end_latitude": 3,
                "end_longitude": 4,
            }]
        )

        inserted = database.insert_trips(trips, 467, self.connection)

        self.assertEqual(inserted, 1)
        params = self.cursor.execute.call_args.args[1]
        self.assertEqual(params, ("42", 467, "2026-06-08T10:00:00", "2026-06-08T10:05:00", 300, 1, 2, 3, 4))
        self.connection.commit.assert_called_once_with()


class TestGetConnection(unittest.TestCase):
    @patch("nextbike_processing.database.psycopg.connect")
    def test_uses_configured_database_settings(self, mock_connect):
        database.get_connection()

        mock_connect.assert_called_once_with(
            host=database.DB_HOST,
            port=database.DB_PORT,
            dbname=database.DB_NAME,
            user=database.DB_USER,
            password=database.DB_PASSWORD,
        )


if __name__ == "__main__":
    unittest.main()
