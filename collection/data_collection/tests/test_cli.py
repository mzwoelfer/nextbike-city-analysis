import os
import unittest
from query_nextbike import NextbikeCLI, AppConfig


class TestNextbikeCLI(unittest.TestCase):
    def test_single_city_id(self):
        cli = NextbikeCLI(env_city_ids=[])
        args = cli.parse_args(["--city-ids", "467"])

        expected_ids = [467]
        self.assertEqual(cli.city_ids, expected_ids)

    def test_multiple_city_ids(self):
        cli = NextbikeCLI(env_city_ids=[])
        args = cli.parse_args(["--city-id", "467", "123"])

        expected_ids = [467, 123]
        self.assertEqual(cli.city_ids, expected_ids)


class TestAppConfig(unittest.TestCase):
    def setUp(self) -> None:
        """Never start a test with set CITY_IDS!"""
        os.environ["CITY_IDS"] = ""

    def tearDown(self):
        """Always remove CITY_IDS after each test"""
        os.environ["CITY_IDS"] = ""

    def test_read_env_ids(self):
        os.environ["CITY_IDS"] = "100,200"
        config = AppConfig()

        expected_ids = [100, 200]
        self.assertEqual(config.city_ids, expected_ids)

    def test_cli_ids_take_precedence(self):
        os.environ["CITY_IDS"] = "100,200"
        cli_ids = [123, 456]
        config = AppConfig(cli_city_ids=cli_ids)

        self.assertEqual(config.city_ids, cli_ids)

    def test_cli_city_ids(self):
        cli_ids = [123, 456]
        config = AppConfig(cli_city_ids=cli_ids)

        self.assertEqual(config.city_ids, cli_ids)

    def test_no_city_ids_raises_error_message(self):
        os.environ["CITY_IDS"] = ""
        with self.assertRaises(ValueError):
            AppConfig(cli_city_ids=[])

    def test_no_city_ids_return_error_message(self):
        os.environ["CITY_IDS"] = ""
        with self.assertRaisesRegex(
            ValueError, "No city ID provided. Use --city-ids or set CITY_IDS in .env."
        ):
            AppConfig(cli_city_ids=[])


if __name__ == "__main__":
    unittest.main()
