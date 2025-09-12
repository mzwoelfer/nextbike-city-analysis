import unittest
from query_nextbike import NextbikeCLI


class TestNextbikeCLI(unittest.TestCase):
    def test_single_city_id(self):
        cli = NextbikeCLI(env_city_ids=[])
        args = cli.parse_args(["--city-ids", "467"])

        expected_ids = [467]
        self.assertEqual(cli.city_ids, expected_ids)


if __name__ == "__main__":
    unittest.main()
