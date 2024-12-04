CREATE TABLE IF NOT EXISTS public.bikes (
    id SERIAL PRIMARY KEY,
    bike_number TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    active BOOLEAN,
    state TEXT,
    bike_type TEXT,
    station_number INTEGER,
    station_uid INTEGER,
    last_updated TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    city_id INTEGER NOT NULL,
    city_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS public.stations (
    id SERIAL PRIMARY KEY,
    uid INTEGER NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    name TEXT NOT NULL,
    spot BOOLEAN NOT NULL,
    station_number INTEGER,
    maintenance BOOLEAN,
    terminal_type TEXT,
    last_updated TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    city_id INTEGER NOT NULL,
    city_name TEXT NOT NULL
);

