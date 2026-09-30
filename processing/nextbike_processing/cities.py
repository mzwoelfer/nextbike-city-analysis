from nextbike_processing.database import get_connection


class CityRepository:
    def __init__(self, connection_factory=get_connection):
        self._connection_factory = connection_factory

    def get_coordinates(self, city_id):
        query = """
            SELECT latitude, longitude
            FROM public.cities
            WHERE city_id = %s;
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (city_id,))
                latitude, longitude = cursor.fetchone()

        return latitude, longitude

    def get_timezone(self, city_id):
        query = """
            SELECT COALESCE(timezone, 'UTC')
            FROM public.cities
            WHERE city_id = %s;
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (city_id,))
                row = cursor.fetchone()

        return row[0] if row else "UTC"


def get_city_coordinates_from_database(city_id):
    return CityRepository().get_coordinates(city_id)


def get_city_timezone_from_database(city_id):
    return CityRepository().get_timezone(city_id)
