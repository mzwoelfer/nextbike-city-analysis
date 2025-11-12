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

    def test_city_class_as_dict(self):
        last_updated = datetime.datetime.now()
        city = City(
            city_id=1,
            city_name="test_city",
            timezone="Europe/Berlin",
            latitude=10.1,
            longitude=20.2,
            set_point_bikes=2,
            available_bikes=3,
            last_updated=last_updated,
        )

        expected_output = {
            "city_id": 1,
            "city_name": "test_city",
            "timezone": "Europe/Berlin",
            "latitude": 10.1,
            "longitude": 20.2,
            "set_point_bikes": 2,
            "available_bikes": 3,
            "last_updated": last_updated,
        }
        self.assertEqual(city.__dict__, expected_output)

    def test_city_class_exists(self):
        city = City(
            city_id=1,
            city_name="test_city",
            timezone="Europe/Berlin",
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

    def test_City_from_api_data_last_updated_is_timestamp_of_execution(self):
        self.assertTrue(self.before <= self.city.last_updated <= self.after)


class TestCity_as_tuple(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.now()
        self.city = City(
            city_id=1,
            city_name="TestTown",
            timezone="Europe/Berlin",
            latitude=10.5,
            longitude=20.5,
            set_point_bikes=50,
            available_bikes=40,
            last_updated=self.now,
        )
        self.as_tuple_result = self.city.as_tuple()

    def test_tuple_length(self):
        self.assertEqual(len(self.as_tuple_result), 8)

    def test_tuple_city_id(self):
        self.assertEqual(self.as_tuple_result[0], 1)

    def test_tuple_city_name(self):
        self.assertEqual(self.as_tuple_result[1], "TestTown")

    def test_tuple_timezone(self):
        self.assertEqual(self.as_tuple_result[2], "Europe/Berlin")

    def test_tuple_latitude(self):
        self.assertEqual(self.as_tuple_result[3], 10.5)

    def test_tuple_longitude(self):
        self.assertEqual(self.as_tuple_result[4], 20.5)

    def test_tuple_set_point_bikes(self):
        self.assertEqual(self.as_tuple_result[5], 50)

    def test_tuple_available_bikes(self):
        self.assertEqual(self.as_tuple_result[6], 40)

    def test_tuple_last_updated(self):
        self.assertEqual(self.as_tuple_result[7], self.now)


class TestCityDefaults(unittest.TestCase):
    def setUp(self):
        # empty payload – triggers all defaults
        self.before = datetime.datetime.now()
        self.city = City.from_api_data({})
        self.after = datetime.datetime.now()

    def test_default_city_id(self):
        self.assertEqual(self.city.city_id, 0)

    def test_default_city_name(self):
        self.assertEqual(self.city.city_name, "Unknown")

    def test_default_timezone(self):
        self.assertEqual(self.city.timezone, "Unknown")

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
