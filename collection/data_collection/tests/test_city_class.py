import unittest
import datetime
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

        self.before = datetime.datetime.now()
        self.city = City.from_api_data(self.api_data)
        self.after = datetime.datetime.now()

    def test_city_class_exists(self):
        city = City(
            city_id=1,
            city_name="test_city",
            timezone="some timezone",
            latitude=50.8,
            longitude=50.8,
            set_point_bikes=1,
            available_bikes=1,
            last_updated=datetime.datetime.now(),
        )
        self.assertIsInstance(city, City)

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

    def test_City_from_api_data_has_last_updated(self):
        self.assertTrue(self.before <= self.city.last_updated <= self.after)
