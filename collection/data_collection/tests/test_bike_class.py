import unittest
import datetime
from query_nextbike import Bike


class TestBikeClass(unittest.TestCase):
    def test_bike_class_exists(self):
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
        self.assertIsInstance(self.bike, Bike)
