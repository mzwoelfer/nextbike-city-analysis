import unittest
import datetime
from query_nextbike import Bike


class TestBikeClass(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.now()
        self.bike = Bike(
            bike_number="12345",
            latitude=47.1,
            longitude=11.2,
            active=True,
            state="ok",
            bike_type="150",
            station_number=999,
            station_uid=555,
            last_updated=self.now,
            city_id=773,
            city_name="Kufstein",
        )
        self.result = self.bike.as_tuple()

    def test_bike_class_exists(self):
        self.assertIsInstance(self.bike, Bike)

    def test_tuple_length(self):
        self.assertEqual(len(self.result), 11)

    def test_tuple_bike_number(self):
        self.assertEqual(self.result[0], "12345")

    def test_tuple_latitude(self):
        self.assertEqual(self.result[1], 47.1)

    def test_tuple_longitude(self):
        self.assertEqual(self.result[2], 11.2)

    def test_tuple_active(self):
        self.assertEqual(self.result[3], True)

    def test_tuple_state(self):
        self.assertEqual(self.result[4], "ok")

    def test_tuple_bike_type(self):
        self.assertEqual(self.result[5], "150")

    def test_tuple_station_number(self):
        self.assertEqual(self.result[6], 999)

    def test_tuple_station_uid(self):
        self.assertEqual(self.result[7], 555)

    def test_tuple_last_updated(self):
        self.assertEqual(self.result[8], self.now)

    def test_tuple_city_id(self):
        self.assertEqual(self.result[9], 773)

    def test_tuple_city_name(self):
        self.assertEqual(self.result[10], "Kufstein")
