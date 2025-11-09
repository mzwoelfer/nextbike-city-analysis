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

    # ----- SECOND BIKE -----
    def test_second_bike_state(self):
        self.assertEqual(self.bikes[0].state, "maintenance")

    # ----- THIRD BIKE -----
    def test_third_bike_city_id(self):
        self.assertEqual(self.bikes[0].city_id, 773)

    # ----- ALL BIKES -----
    def test_all_bikes_have_timestamp(self):
        # Function to iterate places?
        # Then just check each one?
        #
        self.assertEqual(self.bikes[0].last_updated, self.timestamp)


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


class TestBikeClass_as_tuple(unittest.TestCase):
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
