import re
import unittest
import datetime
from database.postgres import PostgresClient
from query_nextbike import City


class TestCityInsertSQL(unittest.TestCase):
    def setUp(self):
        self.table_name = "cities"
        self.sql_statement = PostgresClient.city_sql_insert_statement(self.table_name)

        now = datetime.datetime.now()
        self.city = City(
            city_id=1,
            city_name="TestTown",
            timezone="UTC",
            latitude=10.0,
            longitude=20.0,
            set_point_bikes=5,
            available_bikes=2,
            last_updated=now,
        )

    def test_all_city_dicts_keys_present_in_sql(self):
        for city_key in self.city.__dict__.keys():
            self.assertIn(f"%({city_key})s", self.sql_statement)

    def test_no_unknown_placeholders(self):
        placeholders = re.findall(r"$\((.*?)\)s", self.sql_statement)
        for placeholder in placeholders:
            self.assertIn(placeholder, self.city.__dict__)
