import psycopg
from database.base import AbstractDatabaseClient, register_backend


@register_backend("postgres")
class PostgresClient(AbstractDatabaseClient):
    """Handle postgres entries"""

    # TODO: static methods are duplicated....
    # unify: 3 list with db columns, take data model to generate values

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
    def city_sql_insert_statement(table_name):
        city_sql = f"""
        INSERT INTO {table_name} (
            city_id, city_name, timezone, latitude, longitude, set_point_bikes, available_bikes, last_updated
        )
        VALUES (%(city_id)s, %(city_name)s, %(timezone)s, %(latitude)s, %(longitude)s, %(set_point_bikes)s, %(available_bikes)s, %(last_updated)s)
        ON CONFLICT DO NOTHING;
        """

        return city_sql

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

    @staticmethod
    def bike_sql_insert_statement(table_name):
        bike_sql = f"""
        INSERT INTO {table_name} (
            bike_number, latitude, longitude, active, state, bike_type, station_number, station_uid, last_updated, city_id, city_name
        )
        VALUES (%(bike_number)s, %(latitude)s, %(longitude)s, %(active)s, %(state)s, %(bike_type)s, %(station_number)s, %(station_uid)s, %(last_updated)s, %(city_id)s, %(city_name)s)
        ON CONFLICT DO NOTHING;
        """

        return bike_sql

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

    @staticmethod
    def station_sql_insert_statement(table_name):
        station_sql = f"""
        INSERT INTO {table_name} (
                uid, latitude, longitude, name, spot, station_number, maintenance, terminal_type, last_updated, city_id, city_name
            )
            VALUES (%(uid)s, %(latitude)s, %(longitude)s, %(name)s, %(spot)s, %(station_number)s, %(maintenance)s, %(terminal_type)s, %(last_updated)s, %(city_id)s, %(city_name)s)
            ON CONFLICT DO NOTHING;
        """

        return station_sql
