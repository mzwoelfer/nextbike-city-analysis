import json
import threading
import unittest
from contextlib import contextmanager, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from types import SimpleNamespace

import requests

from query_nextbike import ConsolePrinter, NextbikeAPI, process_nextbike_data


class _StubResponseHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.request_path = self.path
        self.send_response(self.server.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(self.server.payload).encode())

    def log_message(self, format, *args):
        pass


@contextmanager
def local_api_server(payload, status=200):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _StubResponseHandler)
    server.payload = payload
    server.status = status
    server.request_path = None
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", server
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


class TestNextbikeAPI(unittest.TestCase):
    def setUp(self):
        self.sample_response = {
            "countries": [
                {
                    "lat": 50.5811,
                    "lng": 8.66966,
                    "timezone": "Europe/Berlin",
                    "set_point_bikes": 472,
                    "available_bikes": 396,
                    "cities": [
                        {
                            "uid": 467,
                            "name": "Gießen",
                            "places": [
                                {"uid": 1, "name": "Station A"},
                                {"uid": 2, "name": "Station B"},
                            ],
                        }
                    ],
                }
            ]
        }

    def test_extract_places_returns_list(self):
        places = NextbikeAPI.extract_places(self.sample_response)
        self.assertEqual(places, self.sample_response["countries"][0]["cities"][0]["places"])

    def test_extract_places_returns_empty_list_for_missing_all_keys(self):
        data = {}
        places = NextbikeAPI.extract_places(data)
        self.assertEqual(places, [])

    def test_extract_places_returns_empty_list_for_missing_countries_key(self):
        data = {"foo": "bar"}
        places = NextbikeAPI.extract_places(data)
        self.assertEqual(places, [])

    def test_extract_places_returns_empty_list_for_missing_cities_key(self):
        data = {"countries": [{}]}
        places = NextbikeAPI.extract_places(data)
        self.assertEqual(places, [])

    def test_extract_places_returns_empty_list_for_missing_places_key(self):
        data = {"countries": [{"cities": [{}]}]}
        places = NextbikeAPI.extract_places(data)
        self.assertEqual(places, [])

    def test_extract_places_returns_empty_list_for_empty_countries(self):
        self.assertEqual(NextbikeAPI.extract_places({"countries": []}), [])

    def test_fetch_data_returns_json_response(self):
        with local_api_server(self.sample_response) as (url, _):
            api = NextbikeAPI(467)
            api.BASE_URL = url

            result = api.fetch_data()

        self.assertEqual(result, self.sample_response)

    def test_fetch_data_sends_city_id_as_query_parameter(self):
        with local_api_server(self.sample_response) as (url, server):
            api = NextbikeAPI(467)
            api.BASE_URL = url
            api.fetch_data()

        self.assertEqual(server.request_path, "/?city=467")

    def test_fetch_data_raises_for_http_error(self):
        with local_api_server({}, status=400) as (url, _):
            api = NextbikeAPI(467)
            api.BASE_URL = url

            with self.assertRaises(requests.HTTPError):
                api.fetch_data()


class TestProcessNextbikeData(unittest.TestCase):
    def setUp(self):
        data = {
            "countries": [
                {
                    "timezone": "UTC",
                    "cities": [
                        {
                            "uid": 467,
                            "name": "Gießen",
                            "places": [
                                {
                                    "uid": 10,
                                    "number": 20,
                                    "lat": 50.5,
                                    "lng": 8.6,
                                    "bike_list": [{"number": "42", "active": True}],
                                },
                                {
                                    "uid": 11,
                                    "number": 21,
                                    "lat": 50.6,
                                    "lng": 8.7,
                                    "name": "Station",
                                    "bike": False,
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        class StaticAPI:
            def fetch_data(self):
                return data

            @staticmethod
            def extract_places(response):
                return NextbikeAPI.extract_places(response)

        with redirect_stdout(StringIO()):
            self.city, self.bikes, self.stations = process_nextbike_data(StaticAPI())

    def test_city_matches_api_payload(self):
        self.assertEqual((self.city.city_id, self.city.city_name), (467, "Gießen"))

    def test_one_bike_is_created(self):
        self.assertEqual(len(self.bikes), 1)

    def test_bike_matches_api_payload(self):
        self.assertEqual((self.bikes[0].bike_number, self.bikes[0].station_uid), ("42", 10))

    def test_one_station_is_created(self):
        self.assertEqual(len(self.stations), 1)

    def test_station_matches_api_payload(self):
        self.assertEqual((self.stations[0].uid, self.stations[0].name), (11, "Station"))


class TestConsolePrinter(unittest.TestCase):
    def test_print_summary_reports_entry_counts(self):
        city = SimpleNamespace(city_id=467)
        output = StringIO()

        with redirect_stdout(output):
            ConsolePrinter.print_summary(city, [1, 2], [3])

        self.assertIn("Bike entries: 2, Station entries: 1", output.getvalue())
