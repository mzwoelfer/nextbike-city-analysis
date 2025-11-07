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
        city = City.from_api_data(self.api_data)

        self.assertEqual(city.city_id, 773)

    def test_City_from_api_data_has_city_name(self):
        city = City.from_api_data(self.api_data)

        self.assertEqual(city.city_name, "Kufstein")
