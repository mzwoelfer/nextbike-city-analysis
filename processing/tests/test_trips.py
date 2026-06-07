import unittest
from unittest.mock import MagicMock, patch

import networkx as nx
import pandas as pd

from nextbike_processing.trips import (
    build_coordinates_and_timestamps,
    calculate_shortest_path,
    process_and_save_trips,
    remove_gps_errors,
)


class TestBuildCoordinatesAndTimestamps(unittest.TestCase):
    def _make_df(self, start_time, duration, segments):
        return pd.DataFrame([{
            "start_time": start_time,
            "duration": duration,
            "segments": segments,
        }])

    def test_coordinates_are_lon_lat_order(self):
        """GeoJSON requires [lon, lat] — segments come in as [lat, lon]."""
        df = self._make_df("2026-05-30T08:00:00", 120.0, [[52.5, 13.4], [52.6, 13.5]])
        result = build_coordinates_and_timestamps(df)
        coords = result.iloc[0]["coordinates"]
        self.assertEqual(coords[0], [13.4, 52.5])
        self.assertEqual(coords[1], [13.5, 52.6])

    def test_single_segment_produces_one_coordinate_and_one_timestamp(self):
        df = self._make_df("2026-05-30T08:00:00", 0.0, [[52.5, 13.4]])
        result = build_coordinates_and_timestamps(df)
        self.assertEqual(len(result.iloc[0]["coordinates"]), 1)
        self.assertEqual(len(result.iloc[0]["timestamps"]), 1)

    def test_first_timestamp_equals_start_time(self):
        df = self._make_df("2026-05-30T08:00:00", 120.0, [[52.5, 13.4], [52.6, 13.5]])
        result = build_coordinates_and_timestamps(df)
        ts = result.iloc[0]["timestamps"]
        self.assertTrue(ts[0].startswith("2026-05-30T08:00:00"))

    def test_last_timestamp_equals_start_plus_duration(self):
        """With 2 segments and 120s duration the last timestamp is start + 120s."""
        df = self._make_df("2026-05-30T08:00:00", 120.0, [[52.5, 13.4], [52.6, 13.5]])
        result = build_coordinates_and_timestamps(df)
        ts = result.iloc[0]["timestamps"]
        self.assertTrue(ts[-1].startswith("2026-05-30T08:02:00"))

    def test_timestamps_evenly_spaced_for_three_segments(self):
        """3 segments, 120s → increments of 60s each."""
        df = self._make_df(
            "2026-05-30T08:00:00", 120.0,
            [[52.5, 13.4], [52.6, 13.5], [52.7, 13.6]],
        )
        result = build_coordinates_and_timestamps(df)
        ts = result.iloc[0]["timestamps"]
        self.assertEqual(len(ts), 3)
        self.assertTrue(ts[0].startswith("2026-05-30T08:00:00"))
        self.assertTrue(ts[1].startswith("2026-05-30T08:01:00"))
        self.assertTrue(ts[2].startswith("2026-05-30T08:02:00"))

    def test_coordinate_count_matches_segment_count(self):
        segments = [[52.5, 13.4], [52.6, 13.5], [52.7, 13.6], [52.8, 13.7]]
        df = self._make_df("2026-05-30T08:00:00", 180.0, segments)
        result = build_coordinates_and_timestamps(df)
        self.assertEqual(len(result.iloc[0]["coordinates"]), 4)
        self.assertEqual(len(result.iloc[0]["timestamps"]), 4)


class TestRemoveGpsErrors(unittest.TestCase):
    def _make_trips(self, rows):
        return pd.DataFrame(rows, columns=[
            "bike_number", "start_latitude", "start_longitude",
            "end_latitude", "end_longitude", "duration",
        ])

    def test_long_trip_is_always_kept_regardless_of_distance(self):
        """Trips longer than 62s bypass the distance check."""
        trips = self._make_trips([("B1", 52.5, 13.4, 52.5, 13.4, 120.0)])
        self.assertEqual(len(remove_gps_errors(trips)), 1)

    def test_short_trip_at_same_location_is_removed(self):
        trips = self._make_trips([("B1", 52.5, 13.4, 52.5, 13.4, 30.0)])
        self.assertEqual(len(remove_gps_errors(trips)), 0)

    def test_short_trip_far_enough_apart_is_kept(self):
        # 0.01° latitude ≈ 1 113 m — well above the 60 m threshold
        trips = self._make_trips([("B1", 52.5, 13.4, 52.51, 13.4, 30.0)])
        self.assertEqual(len(remove_gps_errors(trips)), 1)

    def test_short_trip_too_close_is_removed(self):
        # 0.0001° latitude ≈ 11 m — below the 60 m threshold
        trips = self._make_trips([("B1", 52.5, 13.4, 52.5001, 13.4, 30.0)])
        self.assertEqual(len(remove_gps_errors(trips)), 0)

    def test_exactly_62s_triggers_distance_check(self):
        trips = self._make_trips([("B1", 52.5, 13.4, 52.5, 13.4, 62.0)])
        self.assertEqual(len(remove_gps_errors(trips)), 0)

    def test_63s_skips_distance_check(self):
        trips = self._make_trips([("B1", 52.5, 13.4, 52.5, 13.4, 63.0)])
        self.assertEqual(len(remove_gps_errors(trips)), 1)

    def test_custom_meter_threshold(self):
        # ~330 m apart — kept with default 60 m threshold, removed with 500 m
        trips = self._make_trips([("B1", 52.5, 13.4, 52.503, 13.4, 30.0)])
        self.assertEqual(len(remove_gps_errors(trips, meter_threshold=60)), 1)
        self.assertEqual(len(remove_gps_errors(trips, meter_threshold=500)), 0)

    def test_mixed_trips(self):
        trips = self._make_trips([
            ("B1", 52.5, 13.4, 52.5, 13.4, 30.0),    # short + same location → removed
            ("B2", 52.5, 13.4, 52.51, 13.4, 30.0),   # short + far apart → kept
            ("B3", 52.5, 13.4, 52.5, 13.4, 120.0),   # long + same location → kept
        ])
        self.assertEqual(len(remove_gps_errors(trips)), 2)


class TestCalculateShortestPath(unittest.TestCase):
    def setUp(self):
        """Tiny synthetic graph: three nodes in a line, bidirectional edges."""
        self.G = nx.MultiDiGraph(crs="epsg:4326")
        self.G.add_node(1, x=13.0, y=52.0)
        self.G.add_node(2, x=13.1, y=52.1)
        self.G.add_node(3, x=13.2, y=52.2)
        self.G.add_edge(1, 2, length=1000)
        self.G.add_edge(2, 1, length=1000)
        self.G.add_edge(2, 3, length=1000)
        self.G.add_edge(3, 2, length=1000)

    def test_path_exists_returns_positive_distance(self):
        distance, segments = calculate_shortest_path(self.G, 52.0, 13.0, 52.1, 13.1)
        self.assertGreater(distance, 0)

    def test_path_exists_returns_segments_as_lat_lon(self):
        """Segments must be [[lat, lon], ...] (internal format, not GeoJSON)."""
        distance, segments = calculate_shortest_path(self.G, 52.0, 13.0, 52.1, 13.1)
        self.assertGreater(len(segments), 0)
        # First segment starts at start node [lat, lon]
        self.assertEqual(segments[0], [52.0, 13.0])
        # Last segment ends at end node
        self.assertEqual(segments[-1], [52.1, 13.1])

    def test_no_path_returns_zero_distance_and_empty_segments(self):
        G = nx.MultiDiGraph(crs="epsg:4326")
        G.add_node(1, x=13.0, y=52.0)
        G.add_node(2, x=13.1, y=52.1)
        # No edges — no path
        distance, segments = calculate_shortest_path(G, 52.0, 13.0, 52.1, 13.1)
        self.assertEqual(distance, 0)
        self.assertEqual(segments, [])

    def test_same_start_and_end_node(self):
        distance, segments = calculate_shortest_path(self.G, 52.0, 13.0, 52.0, 13.0)
        self.assertEqual(distance, 0)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0], [52.0, 13.0])


class TestProcessAndSaveTrips(unittest.TestCase):
    """Tests for the route-concat guard inside process_and_save_trips."""

    def _all_filtered_trips_df(self):
        """One short trip at the same location — remove_gps_errors will drop it, leaving empty unique_pairs."""
        return pd.DataFrame([{
            "bike_number": "B1",
            "start_latitude": 52.5,
            "start_longitude": 13.4,
            "start_time": pd.Timestamp("2026-01-01T08:00:00"),
            "end_latitude": 52.5,
            "end_longitude": 13.4,
            "end_time": pd.Timestamp("2026-01-01T08:00:30"),
            "duration": pd.Timedelta("30s"),
        }])

    def _empty_routes_df(self):
        return pd.DataFrame(
            columns=["start_latitude", "start_longitude", "end_latitude", "end_longitude", "distance", "segments"]
        )

    @patch("nextbike_processing.trips.insert_trips")
    @patch("nextbike_processing.trips.fetch_cached_routes")
    @patch("nextbike_processing.trips.get_connection")
    @patch("nextbike_processing.trips.fetch_trip_data")
    def test_returns_early_when_both_route_dataframes_are_empty(
        self, mock_fetch, mock_get_conn, mock_cached_routes, mock_insert
    ):
        """No trips survive filtering --> both route DataFrames empty --> insert_trips never called."""
        mock_fetch.return_value = self._all_filtered_trips_df()
        mock_get_conn.return_value = MagicMock()
        mock_cached_routes.return_value = self._empty_routes_df()

        process_and_save_trips(1, "2026-01-01", "/tmp")

        mock_insert.assert_not_called()

    @patch("nextbike_processing.trips.insert_trips")
    @patch("nextbike_processing.trips.fetch_cached_routes")
    @patch("nextbike_processing.trips.get_connection")
    @patch("nextbike_processing.trips.fetch_trip_data")
    def test_concat_succeeds_and_insert_called_when_cached_routes_cover_all_pairs(
        self, mock_fetch, mock_get_conn, mock_cached_routes, mock_insert
    ):
        """Cached routes cover all O/D pairs --> concat runs without error --> insert_trips called once."""
        mock_fetch.return_value = pd.DataFrame([{
            "bike_number": "B1",
            "start_latitude": 52.5,
            "start_longitude": 13.4,
            "start_time": pd.Timestamp("2026-01-01T08:00:00"),
            "end_latitude": 52.51,
            "end_longitude": 13.41,
            "end_time": pd.Timestamp("2026-01-01T08:05:00"),
            "duration": pd.Timedelta("5min"),
        }])
        mock_get_conn.return_value = MagicMock()
        mock_cached_routes.return_value = pd.DataFrame([{
            "start_latitude": 52.5,
            "start_longitude": 13.4,
            "end_latitude": 52.51,
            "end_longitude": 13.41,
            "distance": 1200.0,
            "segments": [[52.5, 13.4], [52.51, 13.41]],
        }])

        process_and_save_trips(1, "2026-01-01", "/tmp")

        mock_insert.assert_called_once()


if __name__ == "__main__":
    unittest.main()
