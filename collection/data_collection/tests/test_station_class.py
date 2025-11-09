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

    def test_tuple_length(self):
        self.assertEqual(len(self.result), 11)

    def test_tuple_uid(self):
        self.assertEqual(self.result[0], 1001)

    def test_tuple_latitude(self):
        self.assertEqual(self.result[1], 47.1)

    def test_tuple_longitude(self):
        self.assertEqual(self.result[2], 11.2)

    def test_tuple_name(self):
        self.assertEqual(self.result[3], "Bahnhof")

    def test_tuple_spot(self):
        self.assertEqual(self.result[4], True)

    def test_tuple_station_number(self):
        self.assertEqual(self.result[5], 12345)

    def test_tuple_maintenance(self):
        self.assertEqual(self.result[6], False)

    def test_tuple_terminal_type(self):
        self.assertEqual(self.result[7], "sign")

    def test_tuple_last_updated(self):
        self.assertEqual(self.result[8], self.now)

    def test_tuple_city_id(self):
        self.assertEqual(self.result[9], 773)

    def test_tuple_city_name(self):
        self.assertEqual(self.result[10], "Kufstein")
