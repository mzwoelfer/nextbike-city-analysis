from nextbike_processing.database import get_connection


def get_city_coordinates_from_database(city_id):
    query = f"""
        SELECT latitude, longitude
        FROM public.cities
        WHERE city_id = {city_id};
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            lat, lon = cur.fetchone()

    return lat, lon
