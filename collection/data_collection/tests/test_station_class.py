import unittest
import datetime
from query_nextbike import Station


class TestStationExist(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.now()
        self.station = Station(
            uid=1001,
            latitude=47.1,
            longitude=11.2,
            name="Bahnhof",
            spot=True,
            station_number=12345,
            maintenance=False,
            terminal_type="sign",
            last_updated=self.now,
            city_id=773,
            city_name="Kufstein",
        )
        self.result = self.station.as_tuple()

    def test_Station_exists(self):
        self.assertIsInstance(self.station, Station)
