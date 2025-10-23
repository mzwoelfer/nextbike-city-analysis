import psycopg
from database.base import AbstractDatabaseClient, register_backend

@register_backend("postgres")
class PostgresClient(AbstractDatabaseClient):
    """Handle postgres entries"""

    def __init__(self, config: AppConfig):

        self.connection_string = (
            f"host={config.db_host} dbname={config.db_name} user={config.db_user} password={config.db_password}"
        )

    def insert_city_information(self, city: City):
        city_sql = """
        INSERT INTO public.cities (
            city_id, city_name, timezone, latitude, longitude, set_point_bikes, available_bikes, last_updated
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
        """
        with (
            psycopg.connect(self.connection_string) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(city_sql, city.as_tuple())
            connection.commit()

    def insert_bike_entries(self, bike_entries):
        sql_statement = """
        INSERT INTO public.bikes (
            bike_number, latitude, longitude, active, state, bike_type, station_number, station_uid, last_updated, city_id, city_name
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
        """

        bikes = [bike.as_tuple() for bike in bike_entries]
        with (
            psycopg.connect(self.connection_string) as connection,
            connection.cursor() as cursor,
        ):
            cursor.executemany(sql_statement, bikes)
            connection.commit()

    def insert_station_entries(self, station_entries: list[tuple]):
        sql_statement = """
        INSERT INTO public.stations (
                uid, latitude, longitude, name, spot, station_number, maintenance, terminal_type, last_updated, city_id, city_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """

        stations = [station.as_tuple() for station in station_entries]
        with (
            psycopg.connect(self.connection_string) as connection,
            connection.cursor() as cursor,
        ):
            cursor.executemany(sql_statement, stations)
            connection.commit()
