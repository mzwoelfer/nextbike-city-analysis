import datetime

import psycopg
from database.base import AbstractDatabaseClient, register_backend


@register_backend("postgres")
class PostgresClient(AbstractDatabaseClient):
    """Handle postgres entries"""

    _CITY_COLUMNS = (
        "city_id",
        "city_name",
        "timezone",
        "latitude",
        "longitude",
        "set_point_bikes",
        "available_bikes",
        "last_updated",
    )
    _BIKE_COLUMNS = (
        "bike_number",
        "latitude",
        "longitude",
        "active",
        "state",
        "bike_type",
        "station_number",
        "station_uid",
        "last_updated",
        "city_id",
        "city_name",
    )
    _STATION_COLUMNS = (
        "uid",
        "latitude",
        "longitude",
        "name",
        "spot",
        "station_number",
        "maintenance",
        "terminal_type",
        "last_updated",
        "city_id",
        "city_name",
    )

    def __init__(self, config):
        self.config = config
        self.connection_string = f"host={self.config.db_host} port={self.config.db_port} dbname={self.config.db_name} user={self.config.db_user} password={self.config.db_password}"

    # ----- CITY -----
    def insert_city_information(self, city):
        city_sql = self.city_sql_insert_statement(self.config.db_cities_table)

        with (
            psycopg.connect(self.connection_string) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(city_sql, city.__dict__)
            connection.commit()

    @staticmethod
    def _sql_insert_statement(table_name, columns):
        column_list = ", ".join(columns)
        value_list = ", ".join(f"%({column})s" for column in columns)
        return f"""
        INSERT INTO {table_name} (
            {column_list}
        )
        VALUES ({value_list})
        ON CONFLICT DO NOTHING;
        """

    @classmethod
    def city_sql_insert_statement(cls, table_name):
        return cls._sql_insert_statement(table_name, cls._CITY_COLUMNS)

    # ----- BIKES -----
    def insert_bike_entries(self, bike_entries):
        sql_statement = self.bike_sql_insert_statement(self.config.db_bikes_table)

        bikes = [bike.__dict__ for bike in bike_entries]
        with (
            psycopg.connect(self.connection_string) as connection,
            connection.cursor() as cursor,
        ):
            cursor.executemany(sql_statement, bikes)
            connection.commit()

    @classmethod
    def bike_sql_insert_statement(cls, table_name):
        return cls._sql_insert_statement(table_name, cls._BIKE_COLUMNS)

    # ----- STATIONS -----
    def insert_station_entries(self, station_entries: list[tuple]):
        sql_statement = self.station_sql_insert_statement(self.config.db_stations_table)

        stations = [station.__dict__ for station in station_entries]
        with (
            psycopg.connect(self.connection_string) as connection,
            connection.cursor() as cursor,
        ):
            cursor.executemany(sql_statement, stations)
            connection.commit()

    @classmethod
    def station_sql_insert_statement(cls, table_name):
        return cls._sql_insert_statement(table_name, cls._STATION_COLUMNS)

    # ----- SYNC TIMESTAMPS -----
    def get_last_station_sync(self, city_id: int) -> datetime.datetime | None:
        with psycopg.connect(self.connection_string) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT MAX(last_updated) FROM {self.config.db_stations_table} WHERE city_id = %s",
                    (city_id,),
                )
                result = cursor.fetchone()
                return result[0] if result and result[0] else None

    def get_last_city_sync(self, city_id: int) -> datetime.datetime | None:
        with psycopg.connect(self.connection_string) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT last_updated FROM {self.config.db_cities_table} WHERE city_id = %s",
                    (city_id,),
                )
                result = cursor.fetchone()
                return result[0] if result else None
