import unittest
import datetime
from query_nextbike import Station


class TestStationEmptyPlaces(unittest.TestCase):
    def test_empty_places_returns_empty_list(self):
        stations = Station.build_station_entries(
            places=[],
            city_id=1,
            city_name="X",
            timestamp=datetime.datetime.now(),
        )
        self.assertEqual(stations, [])


class TestStationNoFalseBikeEntries(unittest.TestCase):
    def test_skip_bikes_in_stations(self):
        stations = Station.build_station_entries(
            places=[{"bike": True}, {"bike": True}],
            city_id=1,
            city_name="X",
            timestamp=datetime.datetime.now(),
        )
        self.assertEqual(len(stations), 0)


class TestBuildStationEntries(unittest.TestCase):
    def setUp(self):
        self.timestamp = datetime.datetime.now()
        self.city_id = 773
        self.city_name = "Kufstein"

        self.places = [
            {
                "uid": 1001,
                "lat": 47.5,
                "lng": 12.2,
                "name": "Hauptplatz",
                "spot": True,
                "number": 111,
                "maintenance": False,
                "terminal_type": "sign",
                "bike": False,  # station
            }
        ]

        self.stations = Station.build_station_entries(
            self.places, self.city_id, self.city_name, self.timestamp
        )

    def test_station_uid(self):
        self.assertEqual(self.stations[0].uid, 1001)

    def test_station_city_id(self):
        self.assertEqual(self.stations[0].city_id, 773)

    def test_station_name(self):
        self.assertEqual(self.stations[0].name, "Hauptplatz")

    def test_station_longitude(self):
        self.assertEqual(self.stations[0].longitude, 12.2)

    def test_station_last_updated(self):
        self.assertEqual(self.stations[0].last_updated, self.timestamp)


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


class TestStationDefaults(unittest.TestCase):
    def setUp(self):
        self.timestamp = datetime.datetime.now()
        self.station = Station.build_station_entries(
            places=[{"bike": False}],  # minimal valid "station"
            city_id=1,
            city_name="X",
            timestamp=self.timestamp,
        )[0]

    def test_default_uid(self):
        self.assertEqual(self.station.uid, 0)

    def test_default_latitude(self):
        self.assertEqual(self.station.latitude, 0)

    def test_default_longitude(self):
        self.assertEqual(self.station.longitude, 0)

    def test_default_name(self):
        self.assertEqual(self.station.name, "Unknown")

    def test_default_spot(self):
        self.assertIsNone(self.station.spot)

    def test_default_station_number(self):
        self.assertEqual(self.station.station_number, 0)

    def test_default_maintenance(self):
        self.assertIsNone(self.station.maintenance)

    def test_default_terminal_type(self):
        self.assertEqual(self.station.terminal_type, "Unknown")

    def test_default_last_updated(self):
        self.assertEqual(self.station.last_updated, self.timestamp)

    def test_default_city_id(self):
        self.assertEqual(self.station.city_id, 1)

    def test_default_city_name(self):
        self.assertEqual(self.station.city_name, "X")
