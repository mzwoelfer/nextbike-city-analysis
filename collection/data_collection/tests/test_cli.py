import unittest
from query_nextbike import NextbikeCLI


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

    def test_fallback_to_env(self):
        cli = NextbikeCLI(env_city_ids=[123, 456])
        args = cli.parse_args([])

        expected_ids = [123, 456]
        self.assertEqual(cli.city_ids, expected_ids)

    def test_no_city_id_and_no_envprovides_error_message(self):
        cli = NextbikeCLI(env_city_ids=[])
        with self.assertRaisesRegex(
            ValueError,
            "No city ID provided. Use --city-ids or set CITY_IDS in .env.",
        ):
            cli.parse_args([])


if __name__ == "__main__":
    unittest.main()
