import unittest
from unittest.mock import MagicMock, patch

from nextbike_processing.cities import (
    get_city_coordinates_from_database,
    get_city_timezone_from_database,
)


class TestCityQueries(unittest.TestCase):
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
        return connection, cursor

    @patch("nextbike_processing.cities.get_connection")
    def test_get_city_coordinates_returns_database_values(self, mock_get_connection):
        connection, cursor = self._connection((50.5, 8.6))
        mock_get_connection.return_value = connection

        result = get_city_coordinates_from_database(467)

        self.assertEqual(result, (50.5, 8.6))
        cursor.execute.assert_called_once()
        self.assertEqual(cursor.execute.call_args.args[1], (467,))

    @patch("nextbike_processing.cities.get_connection")
    def test_get_city_timezone_returns_database_value(self, mock_get_connection):
        connection, _ = self._connection(("Europe/Berlin",))
        mock_get_connection.return_value = connection

        self.assertEqual(get_city_timezone_from_database(467), "Europe/Berlin")

    @patch("nextbike_processing.cities.get_connection")
    def test_get_city_timezone_defaults_to_utc_without_a_row(self, mock_get_connection):
        connection, _ = self._connection(None)
        mock_get_connection.return_value = connection

        self.assertEqual(get_city_timezone_from_database(467), "UTC")


if __name__ == "__main__":
    unittest.main()
