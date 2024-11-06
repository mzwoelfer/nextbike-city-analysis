CREATE DATABASE nextbike_data;

\c nextbike_data;

GRANT ALL PRIVILEGES ON SCHEMA public TO bike_admin;


CREATE TABLE public.bikes (
    id SERIAL PRIMARY KEY,
    bike_number TEXT NOT NULL,
    bike_type INTEGER NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    active BOOLEAN NOT NULL,
    state TEXT,
    last_updated BIGINT,
    UNIQUE(bike_number, timestamp)
);

CREATE TABLE public.stations (
    id SERIAL PRIMARY KEY,
    uid INTEGER NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    name TEXT,
    spot BOOLEAN NOT NULL,
    station_number INTEGER,
    maintenance BOOLEAN,
    terminal_type TEXT,
    last_updated BIGINT,
    UNIQUE(uid, timestamp)
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bike_admin;
