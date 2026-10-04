import unittest
import datetime
from query_nextbike import Bike


class TestBikeClass_Entries_from_place_multiple_bikes(unittest.TestCase):
    def setUp(self):
        self.timestamp = datetime.datetime.now()
        self.city_id = 773
        self.city_name = "Kufstein"

        self.places = [
            {
                "uid": 1002,
                "lat": 48.0,
                "lng": 13.0,
                "number": 102,
                "bike_list": [
                    {
                        "number": "B002",
                        "active": False,
                        "state": "maintenance",
                        "bike_type": "237",
                    },
                    {
                        "number": "B003",
                        "active": True,
                        "state": "ok",
                        "bike_type": "150",
                    },
                ],
            },
        ]

        self.bikes = Bike.bike_entries_from_place(
            self.places, self.city_id, self.city_name, self.timestamp
        )

    def test_first_bike_state(self):
        self.assertEqual(self.bikes[0].state, "maintenance")

    def test_second_bike_number(self):
        self.assertEqual(self.bikes[1].bike_number, "B003")

    def test_second_bike_city_id(self):
        self.assertEqual(self.bikes[1].city_id, self.city_id)

    def test_all_bikes_have_timestamp(self):
        self.assertEqual(
            [bike.last_updated for bike in self.bikes],
            [self.timestamp, self.timestamp],
        )


class TestBikeClass_Entries_from_place(unittest.TestCase):
    def setUp(self):
        self.timestamp = datetime.datetime.now()
        self.city_id = 773
        self.city_name = "Kufstein"

        self.places = [
            {
                "uid": 1001,
                "lat": 47.0,
                "lng": 12.0,
                "number": 101,
                "bike_list": [
                    {
                        "number": "B001",
                        "active": True,
                        "state": "ok",
                        "bike_type": "150",
                    }
                ],
            },
        ]

        self.bikes = Bike.bike_entries_from_place(
            self.places, self.city_id, self.city_name, self.timestamp
        )

    def test_number_of_bike_entries(self):
        self.assertEqual(len(self.bikes), 1)

    def test_bike_number(self):
        self.assertEqual(self.bikes[0].bike_number, "B001")

    def test_bike_station_uid(self):
        self.assertEqual(self.bikes[0].station_uid, 1001)

    def test_bike_station_number(self):
        self.assertEqual(self.bikes[0].station_number, 101)

    def test_bike_has_correct_lat(self):
        self.assertEqual(self.bikes[0].latitude, 47.0)

    def test_bike_has_correct_longitude(self):
        self.assertEqual(self.bikes[0].longitude, 12.0)


class TestBikeDefaults(unittest.TestCase):
    def setUp(self):
        # minimal viable input: empty bike_list entry with no fields
        self.timestamp = datetime.datetime.now()
        bikes = Bike.bike_entries_from_place(
            places=[{"bike_list": [{}]}],
            city_id=1,
            city_name="X",
            timestamp=self.timestamp,
        )
        self.bike = bikes[0]

    def test_default_bike_number(self):
        self.assertEqual(self.bike.bike_number, "")

    def test_default_latitude(self):
        self.assertEqual(self.bike.latitude, 0)

    def test_default_longitude(self):
        self.assertEqual(self.bike.longitude, 0)

    def test_default_active(self):
        self.assertIsNone(self.bike.active)

    def test_default_state(self):
        self.assertEqual(self.bike.state, "")

    def test_default_bike_type(self):
        self.assertEqual(self.bike.bike_type, "")

    def test_default_station_number(self):
        self.assertEqual(self.bike.station_number, 0)

    def test_default_station_uid(self):
        self.assertEqual(self.bike.station_uid, 0)

    def test_default_last_updated(self):
        self.assertEqual(self.bike.last_updated, self.timestamp)

    def test_default_city_id(self):
        self.assertEqual(self.bike.city_id, 1)

    def test_default_city_name(self):
        self.assertEqual(self.bike.city_name, "X")
