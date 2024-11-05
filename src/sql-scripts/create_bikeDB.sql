CREATE DATABASE bikes
    WITH
    OWNER = bike_admin
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'  -- Match template database collation
    LC_CTYPE = 'en_US.UTF-8'    -- Match template database collation
    TEMPLATE = template0        -- Allow custom settings
    CONNECTION LIMIT = -1;

\c bikes

GRANT ALL PRIVILEGES ON SCHEMA public TO bike_admin;

-- Table: public.bikeLocations
CREATE TABLE public."bikeLocations" (
    id SERIAL PRIMARY KEY,
    "bikeId" TEXT NOT NULL,
    "timestamp" TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    "stationId" TEXT NOT NULL,
    "vehicleTypeId" TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL
)
TABLESPACE pg_default;

-- Table: public.stations
CREATE TABLE public.stations (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    "stationId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "firstListed" TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    "lastListed" TIMESTAMP WITHOUT TIME ZONE NOT NULL
)
TABLESPACE pg_default;

-- Grant privileges to bike_admin on all tables in the public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bike_admin;