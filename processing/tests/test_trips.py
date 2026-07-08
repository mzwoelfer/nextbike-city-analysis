import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd

from nextbike_processing import trips as trips_module


class TestCityIsoFormatting(unittest.TestCase):
    def test_to_city_isoformat_converts_utc_to_city_offset(self):
        berlin = trips_module.ZoneInfo("Europe/Berlin")
        result = trips_module._to_city_isoformat(
            pd.Timestamp("2026-06-08T10:00:00+00:00"),
            berlin,
        )
        self.assertEqual(result, "2026-06-08T12:00:00+02:00")


class TestFetchTripData(unittest.TestCase):
    @patch("nextbike_processing.trips.pd.read_sql_query")
    @patch("nextbike_processing.trips.get_connection")
    def test_fetch_trip_data_uses_city_timezone_date_filter(self, mock_get_connection, mock_read_sql_query):
        mock_conn_cm = MagicMock()
        mock_conn_cm.__enter__.return_value = MagicMock()
        mock_conn_cm.__exit__.return_value = False
        mock_get_connection.return_value = mock_conn_cm

        mock_read_sql_query.return_value = pd.DataFrame(
            [
                {
                    "bike_number": "42",
                    "start_latitude": 52.5,
                    "start_longitude": 13.4,
                    "start_time": "2026-06-08T10:00:00+00:00",
                    "end_latitude": 52.51,
                    "end_longitude": 13.41,
                    "end_time": "2026-06-08T10:05:00+00:00",
                }
            ]
        )

        df = trips_module.fetch_trip_data(467, "2026-06-08")

        query = mock_read_sql_query.call_args.args[0]
        params = mock_read_sql_query.call_args.kwargs["params"]
        self.assertIn("DATE(b.last_updated AT TIME ZONE c.timezone)", query)
        self.assertEqual(params, (467, "2026-06-08"))
        self.assertAlmostEqual(df.iloc[0]["duration"].total_seconds(), 300.0)


class TestCalculateShortestPath(unittest.TestCase):
    @patch("nextbike_processing.trips.nx.shortest_path")
    @patch("nextbike_processing.trips.nx.shortest_path_length")
    @patch("nextbike_processing.trips.ox.distance.nearest_nodes")
    def test_returns_distance_and_segments(self, mock_nearest_nodes, mock_shortest_path_length, mock_shortest_path):
        graph = SimpleNamespace(
            nodes={
                1: {"y": 52.0, "x": 13.0},
                2: {"y": 52.1, "x": 13.1},
            }
        )
        mock_nearest_nodes.side_effect = [1, 2]
        mock_shortest_path_length.return_value = 1000.0
        mock_shortest_path.return_value = [1, 2]

        distance, segments = trips_module.calculate_shortest_path(graph, 52.0, 13.0, 52.1, 13.1)

        self.assertEqual(distance, 1000.0)
        self.assertEqual(segments, [[52.0, 13.0], [52.1, 13.1]])

    @patch("nextbike_processing.trips.ox.distance.nearest_nodes")
    def test_returns_none_and_empty_when_node_not_in_graph(self, mock_nearest_nodes):
        graph = SimpleNamespace(nodes={1: {"y": 52.0, "x": 13.0}})
        mock_nearest_nodes.side_effect = [1, 2]

        distance, segments = trips_module.calculate_shortest_path(graph, 52.0, 13.0, 52.1, 13.1)

        self.assertIsNone(distance)
        self.assertEqual(segments, [])

    @patch("nextbike_processing.trips.nx.shortest_path_length")
    @patch("nextbike_processing.trips.ox.distance.nearest_nodes")
    def test_returns_none_and_empty_on_no_path(self, mock_nearest_nodes, mock_shortest_path_length):
        graph = SimpleNamespace(
            nodes={
                1: {"y": 52.0, "x": 13.0},
                2: {"y": 52.1, "x": 13.1},
            }
        )
        mock_nearest_nodes.side_effect = [1, 2]
        mock_shortest_path_length.side_effect = trips_module.nx.NetworkXNoPath

        distance, segments = trips_module.calculate_shortest_path(graph, 52.0, 13.0, 52.1, 13.1)

        self.assertIsNone(distance)
        self.assertEqual(segments, [])


class TestProcessAndSaveTrips(unittest.TestCase):
    def _connection_cm(self):
        cm = MagicMock()
        cm.__enter__.return_value = MagicMock(name="conn")
        cm.__exit__.return_value = False
        return cm

    def _sample_trip_rows(self):
        return pd.DataFrame(
            [
                {
                    "bike_number": "42",
                    "start_latitude": 52.5,
                    "start_longitude": 13.4,
                    "start_time": pd.Timestamp("2026-06-08T10:00:00+00:00"),
                    "end_latitude": 52.51,
                    "end_longitude": 13.41,
                    "end_time": pd.Timestamp("2026-06-08T10:05:00+00:00"),
                    "duration": pd.Timedelta("5min"),
                }
            ]
        )

    def _sample_cached_routes(self):
        return pd.DataFrame(
            [
                {
                    "start_latitude": 52.5,
                    "start_longitude": 13.4,
                    "end_latitude": 52.51,
                    "end_longitude": 13.41,
                    "distance": 1200.0,
                    "segments": [[52.5, 13.4], [52.51, 13.41]],
                }
            ]
        )

    @patch("nextbike_processing.trips.insert_trips")
    @patch("nextbike_processing.trips.get_uncached_route_pairs")
    @patch("nextbike_processing.trips.get_cached_routes")
    @patch("nextbike_processing.trips.get_connection")
    @patch("nextbike_processing.trips.fetch_trip_data")
    def test_returns_early_when_no_routes_available(
        self,
        mock_fetch_trip_data,
        mock_get_connection,
        mock_get_cached_routes,
        mock_get_uncached_route_pairs,
        mock_insert_trips,
    ):
        mock_fetch_trip_data.return_value = self._sample_trip_rows()
        mock_get_connection.return_value = self._connection_cm()
        mock_get_cached_routes.return_value = pd.DataFrame(
            columns=["start_latitude", "start_longitude", "end_latitude", "end_longitude", "distance", "segments"]
        )
        mock_get_uncached_route_pairs.return_value = pd.DataFrame(
            columns=["start_latitude", "start_longitude", "end_latitude", "end_longitude"]
        )

        trips_module.process_and_save_trips(467, "2026-06-08", "/tmp", export_files=False)

        mock_insert_trips.assert_not_called()

    @patch("nextbike_processing.trips.insert_trips")
    @patch("nextbike_processing.trips.get_uncached_route_pairs")
    @patch("nextbike_processing.trips.get_cached_routes")
    @patch("nextbike_processing.trips.get_connection")
    @patch("nextbike_processing.trips.fetch_trip_data")
    def test_inserts_trips_when_cached_routes_exist(
        self,
        mock_fetch_trip_data,
        mock_get_connection,
        mock_get_cached_routes,
        mock_get_uncached_route_pairs,
        mock_insert_trips,
    ):
        mock_fetch_trip_data.return_value = self._sample_trip_rows()
        mock_get_connection.return_value = self._connection_cm()
        mock_get_cached_routes.return_value = self._sample_cached_routes()
        mock_get_uncached_route_pairs.return_value = pd.DataFrame(
            columns=["start_latitude", "start_longitude", "end_latitude", "end_longitude"]
        )

        trips_module.process_and_save_trips(467, "2026-06-08", "/tmp", export_files=False)

        mock_insert_trips.assert_called_once()
        inserted_df = mock_insert_trips.call_args.args[0]
        self.assertAlmostEqual(inserted_df.iloc[0]["duration"], 300.0)

    @patch("nextbike_processing.trips.save_gzipped_csv")
    @patch("nextbike_processing.trips.save_gzipped_geojson")
    @patch("nextbike_processing.trips.get_city_timezone_from_database")
    @patch("nextbike_processing.trips.insert_trips")
    @patch("nextbike_processing.trips.get_uncached_route_pairs")
    @patch("nextbike_processing.trips.get_cached_routes")
    @patch("nextbike_processing.trips.get_connection")
    @patch("nextbike_processing.trips.fetch_trip_data")
    def test_export_writes_offset_aware_timestamps_and_timezone(
        self,
        mock_fetch_trip_data,
        mock_get_connection,
        mock_get_cached_routes,
        mock_get_uncached_route_pairs,
        _mock_insert_trips,
        mock_get_city_timezone,
        mock_save_geojson,
        mock_save_csv,
    ):
        mock_fetch_trip_data.return_value = self._sample_trip_rows()
        mock_get_connection.return_value = self._connection_cm()
        mock_get_cached_routes.return_value = self._sample_cached_routes()
        mock_get_uncached_route_pairs.return_value = pd.DataFrame(
            columns=["start_latitude", "start_longitude", "end_latitude", "end_longitude"]
        )
        mock_get_city_timezone.return_value = "Europe/Berlin"

        trips_module.process_and_save_trips(467, "2026-06-08", "/tmp", export_files=True)

        geojson_payload = mock_save_geojson.call_args.args[1]
        props = geojson_payload["features"][0]["properties"]
        self.assertEqual(props["timezone"], "Europe/Berlin")
        self.assertTrue(props["start_time"].endswith("+02:00"))
        self.assertTrue(props["end_time"].endswith("+02:00"))

        csv_df = mock_save_csv.call_args.args[1]
        self.assertIn("timezone", csv_df.columns)
        self.assertEqual(csv_df.iloc[0]["timezone"], "Europe/Berlin")
        self.assertTrue(csv_df.iloc[0]["start_time"].endswith("+02:00"))


if __name__ == "__main__":
    unittest.main()
