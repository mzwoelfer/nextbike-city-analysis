from nextbike_processing.database import get_connection


def get_city_coordinates_from_database(city_id):
    query = """
        SELECT latitude, longitude
        FROM public.cities
        WHERE city_id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (city_id,))
            lat, lon = cur.fetchone()

    return lat, lon
