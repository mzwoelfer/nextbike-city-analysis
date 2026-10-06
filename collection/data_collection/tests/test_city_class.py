import unittest
import datetime
from zoneinfo import ZoneInfo
from query_nextbike import City


class TestCityDataClass(unittest.TestCase):
    def setUp(self):
        self.api_data = {
            "countries": [
                {
                    "lat": 47.4875,
                    "lng": 12.0383,
                    "timezone": "Europe/Berlin",
                    "set_point_bikes": 134,
                    "available_bikes": 87,
                    "cities": [
                        {
                            "uid": 773,
                            "name": "Kufstein",
                        }
                    ],
                }
            ]
        }

        self.before = datetime.datetime.now(ZoneInfo("UTC"))
        self.city = City.from_api_data(self.api_data)
        self.after = datetime.datetime.now(ZoneInfo("UTC"))

    def test_City_from_api_data_has_city_id(self):
        self.assertEqual(self.city.city_id, 773)

    def test_City_from_api_data_has_city_name(self):
        self.assertEqual(self.city.city_name, "Kufstein")

    def test_City_from_api_data_has_timezone(self):
        self.assertEqual(self.city.timezone, "Europe/Berlin")

    def test_City_from_api_data_has_latitude(self):
        self.assertEqual(self.city.latitude, 47.4875)

    def test_City_from_api_data_has_longitude(self):
        self.assertEqual(self.city.longitude, 12.0383)

    def test_City_from_api_data_has_set_point_bikes(self):
        self.assertEqual(self.city.set_point_bikes, 134)

    def test_City_from_api_data_has_available_bikes(self):
        self.assertEqual(self.city.available_bikes, 87)

    def test_City_from_api_data_last_updated_is_timestamp_of_execution(self):
        self.assertTrue(self.before <= self.city.last_updated <= self.after)


class TestCityDefaults(unittest.TestCase):
    def setUp(self):
        # empty payload – triggers all defaults
        self.before = datetime.datetime.now(ZoneInfo("UTC"))
        self.city = City.from_api_data({})
        self.after = datetime.datetime.now(ZoneInfo("UTC"))

    def test_default_city_id(self):
        self.assertEqual(self.city.city_id, 0)

    def test_default_city_name(self):
        self.assertEqual(self.city.city_name, "Unknown")

    def test_default_timezone(self):
        self.assertEqual(self.city.timezone, "UTC")

    def test_default_latitude(self):
        self.assertEqual(self.city.latitude, 0)

    def test_default_longitude(self):
        self.assertEqual(self.city.longitude, 0)

    def test_default_set_point_bikes(self):
        self.assertEqual(self.city.set_point_bikes, 0)

    def test_default_available_bikes(self):
        self.assertEqual(self.city.available_bikes, 0)

    def test_last_updated_set(self):
        # last_updated is set to "now"
        self.assertTrue(self.before <= self.city.last_updated <= self.after)
