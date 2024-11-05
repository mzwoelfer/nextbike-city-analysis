-- Drop the existing bikes database if it exists
-- DROP DATABASE IF EXISTS bikes;

CREATE DATABASE bikes
    WITH
    OWNER = bike_admin
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0
    CONNECTION LIMIT = -1;

-- Connect to bikes database
\c bikes

-- bike_admin has necessary privileges
GRANT ALL PRIVILEGES ON SCHEMA public TO bike_admin;

CREATE TABLE public."bikeLocations" (
    id SERIAL PRIMARY KEY,
    "bikeId" TEXT NOT NULL,
    "timestamp" TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    "stationId" TEXT NOT NULL,
    "vehicleTypeId" TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    "is_reserved" BOOLEAN NOT NULL,
    "is_disabled" BOOLEAN NOT NULL,
    "version" TEXT NOT NULL,
    "last_updated" BIGINT NOT NULL,                            -- UNIX timestamp
    "ttl" INTEGER NOT NULL
)
TABLESPACE pg_default;

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
