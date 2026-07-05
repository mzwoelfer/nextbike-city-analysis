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

CREATE TABLE IF NOT EXISTS public.cities (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL UNIQUE,
    city_name TEXT NOT NULL,
    timezone TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    set_point_bikes INTEGER NOT NULL,
    available_bikes INTEGER NOT NULL,
    last_updated TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS public.routes (
    id SERIAL PRIMARY KEY,
    start_latitude DOUBLE PRECISION NOT NULL,
    start_longitude DOUBLE PRECISION NOT NULL,
    end_latitude DOUBLE PRECISION NOT NULL,
    end_longitude DOUBLE PRECISION NOT NULL,
    distance_meters DOUBLE PRECISION NOT NULL,
    coordinates JSONB NOT NULL,
    UNIQUE (start_latitude, start_longitude, end_latitude, end_longitude)
);

CREATE TABLE IF NOT EXISTS public.trips (
    id SERIAL PRIMARY KEY,
    bike_number TEXT NOT NULL,
    city_id INTEGER NOT NULL,
    start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    end_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    duration_seconds DOUBLE PRECISION NOT NULL,
    route_id INTEGER REFERENCES public.routes(id),
    UNIQUE (bike_number, city_id, start_time)
);