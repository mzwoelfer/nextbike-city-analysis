import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

from query_nextbike import ConsolePrinter, NextbikeAPI, process_nextbike_data


class TestNextbikeAPI(unittest.TestCase):
    def setUp(self):
        self.sample_response = {
            "countries": [
                {
                    "lat": 50.5811,
                    "lng": 8.66966,
                    "timezone": "Europe/Berlin",
                    "set_point_bikes": 472,
                    "available_bikes": 396,
                    "cities": [
                        {
                            "uid": 467,
                            "name": "Gießen",
                            "places": [
                                {"uid": 1, "name": "Station A"},
                                {"uid": 2, "name": "Station B"},
                            ],
                        }
                    ],
                }
            ]
        }

    def test_extract_places_returns_list(self):
        places = NextbikeAPI.extract_places(self.sample_response)
        self.assertEqual(len(places), 2)

    def test_extract_places_returns_empty_list_for_missing_all_keys(self):
        data = {}
        places = NextbikeAPI.extract_places(data)
        self.assertEqual(places, [])

    def test_extract_places_returns_empty_list_for_missing_countries_key(self):
        data = {"foo": "bar"}
        places = NextbikeAPI.extract_places(data)
        self.assertEqual(places, [])

    def test_extract_places_returns_empty_list_for_missing_cities_key(self):
        data = {"countries": [{}]}
        places = NextbikeAPI.extract_places(data)
        self.assertEqual(places, [])

    def test_extract_places_returns_empty_list_for_missing_places_key(self):
        data = {"countries": [{"cities": [{}]}]}
        places = NextbikeAPI.extract_places(data)
        self.assertEqual(places, [])

    def test_extract_places_returns_empty_list_for_empty_countries(self):
        self.assertEqual(NextbikeAPI.extract_places({"countries": []}), [])

    @patch("query_nextbike.requests.get")
    def test_fetch_data_uses_city_parameter_and_returns_json(self, mock_get):
        response = MagicMock()
        response.json.return_value = self.sample_response
        mock_get.return_value = response

        result = NextbikeAPI(467).fetch_data()

        mock_get.assert_called_once_with(NextbikeAPI.BASE_URL, params={"city": 467})
        response.raise_for_status.assert_called_once_with()
        self.assertEqual(result, self.sample_response)

    @patch("query_nextbike.requests.get")
    def test_fetch_data_propagates_http_error(self, mock_get):
        response = MagicMock()
        response.raise_for_status.side_effect = ValueError("bad response")
        mock_get.return_value = response

        with self.assertRaisesRegex(ValueError, "bad response"):
            NextbikeAPI(467).fetch_data()

        response.json.assert_not_called()

    @patch("query_nextbike.ConsolePrinter.print_summary")
    def test_process_nextbike_data_builds_city_bikes_and_stations(self, mock_summary):
        data = {
            "countries": [
                {
                    "timezone": "UTC",
                    "cities": [
                        {
                            "uid": 467,
                            "name": "Gießen",
                            "places": [
                                {
                                    "uid": 10,
                                    "number": 20,
                                    "lat": 50.5,
                                    "lng": 8.6,
                                    "bike_list": [{"number": "42", "active": True}],
                                },
                                {
                                    "uid": 11,
                                    "number": 21,
                                    "lat": 50.6,
                                    "lng": 8.7,
                                    "name": "Station",
                                    "bike": False,
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        api = NextbikeAPI(467)
        with patch.object(api, "fetch_data", return_value=data):
            city, bikes, stations = process_nextbike_data(api)

        self.assertEqual((city.city_id, city.city_name), (467, "Gießen"))
        self.assertEqual(len(bikes), 1)
        self.assertEqual((bikes[0].bike_number, bikes[0].station_uid), ("42", 10))
        self.assertEqual(len(stations), 1)
        self.assertEqual((stations[0].uid, stations[0].name), (11, "Station"))
        mock_summary.assert_called_once_with(city, bikes, stations)


class TestConsolePrinter(unittest.TestCase):
    def test_print_summary_reports_entry_counts(self):
        city = MagicMock()
        output = StringIO()

        with redirect_stdout(output):
            ConsolePrinter.print_summary(city, [1, 2], [3])

        self.assertIn("Bike entries: 2, Station entries: 1", output.getvalue())
