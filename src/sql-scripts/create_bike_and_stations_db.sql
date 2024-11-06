CREATE DATABASE nextbike_data;

\c nextbike_data;

GRANT ALL PRIVILEGES ON SCHEMA public TO bike_admin;


CREATE TABLE public.bikes (
    id SERIAL PRIMARY KEY,
    bike_number TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    active BOOLEAN,
    state TEXT,
    bike_type TEXT,
    last_updated TIMESTAMP WITHOUT TIME ZONE NOT NULL
)

CREATE TABLE public.stations (
    id SERIAL PRIMARY KEY,
    uid INTEGER NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    name TEXT NOT NULL,
    spot BOOLEAN NOT NULL,
    station_number INTEGER,
    maintenance BOOLEAN,
    terminal_type TEXT,
    last_updated TIMESTAMP WITHOUT TIME ZONE NOT NULL
)

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bike_admin;
