import unittest
from query_nextbike import NextbikeAPI


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
