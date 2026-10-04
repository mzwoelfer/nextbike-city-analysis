import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from nextbike_processing.stations import fetch_station_data, process_and_save_stations


class TestStationProcessing(unittest.TestCase):
    def _connection(self, row):
        cursor = MagicMock()
        cursor.fetchone.return_value = row
        cursor_context = MagicMock()
        cursor_context.__enter__.return_value = cursor
        cursor_context.__exit__.return_value = False
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.__exit__.return_value = False
        connection.cursor.return_value = cursor_context
        return connection

    @patch("nextbike_processing.stations.pd.read_sql_query")
    @patch("nextbike_processing.stations.get_connection")
    def test_fetch_station_data_formats_city_timezone_and_query_params(
        self, mock_get_connection, mock_read_sql_query
    ):
        connection = self._connection(("Europe/Berlin",))
        mock_get_connection.return_value = connection
        mock_read_sql_query.return_value = pd.DataFrame(
            {"minute": [pd.Timestamp("2026-06-08 10:30:00")], "bike_count": [2]}
        )

        result = fetch_station_data(467, "2026-06-08")

        self.assertEqual(result.iloc[0]["minute"], "2026-06-08T10:30:00+02:00")
        self.assertEqual(result.iloc[0]["timezone"], "Europe/Berlin")
        self.assertEqual(mock_read_sql_query.call_args.kwargs["params"], (467, 467, "2026-06-08", 467, "2026-06-08", 467, "2026-06-08"))

    @patch("nextbike_processing.stations.pd.read_sql_query")
    @patch("nextbike_processing.stations.get_connection")
    def test_fetch_station_data_defaults_to_utc_without_city_row(
        self, mock_get_connection, mock_read_sql_query
    ):
        mock_get_connection.return_value = self._connection(None)
        mock_read_sql_query.return_value = pd.DataFrame(
            {"minute": [pd.Timestamp("2026-06-08 10:30:00")]}
        )

        result = fetch_station_data(467, "2026-06-08")

        self.assertEqual(result.iloc[0]["minute"], "2026-06-08T10:30:00+00:00")
        self.assertEqual(result.iloc[0]["timezone"], "UTC")

    @patch("nextbike_processing.stations.save_gzipped_csv")
    @patch("nextbike_processing.stations.fetch_station_data")
    def test_process_and_save_stations_exports_when_requested(
        self, mock_fetch_station_data, mock_save_csv
    ):
        station_data = pd.DataFrame({"uid": [1]})
        mock_fetch_station_data.return_value = station_data

        process_and_save_stations(467, "2026-06-08", "/tmp/export", export_files=True)

        mock_fetch_station_data.assert_called_once_with(467, "2026-06-08")
        mock_save_csv.assert_called_once_with(
            "/tmp/export/467_stations_2026-06-08.csv.gz", station_data
        )

    @patch("nextbike_processing.stations.save_gzipped_csv")
    @patch("nextbike_processing.stations.fetch_station_data")
    def test_process_and_save_stations_skips_export_by_default(
        self, mock_fetch_station_data, mock_save_csv
    ):
        mock_fetch_station_data.return_value = pd.DataFrame()

        process_and_save_stations(467, "2026-06-08", None)

        mock_save_csv.assert_not_called()


if __name__ == "__main__":
    unittest.main()
