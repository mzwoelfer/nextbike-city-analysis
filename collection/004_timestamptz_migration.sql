-- Migration: convert all naive TIMESTAMP columns to TIMESTAMPTZ.
--
-- Existing data was collected with the server running UTC and stored without
-- timezone info, so every value is UTC in disguise.  We annotate it as UTC
-- (AT TIME ZONE 'UTC') which produces a proper TIMESTAMPTZ that PostgreSQL
-- stores as one unambiguous instant.
--
-- Run against the live database BEFORE restarting the collector:
--   psql -h localhost -p 5432 -U <user> -d <dbname> -f 004_timestamptz_migration.sql

BEGIN;

-- ── bikes ────────────────────────────────────────────────────────────────────
-- Cannot use ALTER COLUMN … USING with a JOIN, so: add temp col, populate,
-- drop old, rename.
ALTER TABLE public.bikes ADD COLUMN last_updated_tz TIMESTAMPTZ;
UPDATE public.bikes SET last_updated_tz = last_updated AT TIME ZONE 'UTC';
ALTER TABLE public.bikes DROP COLUMN last_updated;
ALTER TABLE public.bikes RENAME COLUMN last_updated_tz TO last_updated;
ALTER TABLE public.bikes ALTER COLUMN last_updated SET NOT NULL;

-- ── stations ─────────────────────────────────────────────────────────────────
ALTER TABLE public.stations ADD COLUMN last_updated_tz TIMESTAMPTZ;
UPDATE public.stations SET last_updated_tz = last_updated AT TIME ZONE 'UTC';
ALTER TABLE public.stations DROP COLUMN last_updated;
ALTER TABLE public.stations RENAME COLUMN last_updated_tz TO last_updated;
ALTER TABLE public.stations ALTER COLUMN last_updated SET NOT NULL;

-- ── cities ───────────────────────────────────────────────────────────────────
-- No join needed; timezone is on the same row, so USING clause is fine.
ALTER TABLE public.cities
    ALTER COLUMN last_updated TYPE TIMESTAMPTZ
    USING last_updated AT TIME ZONE 'UTC';

-- ── trips ────────────────────────────────────────────────────────────────────
-- Dropping start_time also drops the UNIQUE constraint that references it,
-- so we recreate it at the end.
ALTER TABLE public.trips ADD COLUMN start_time_tz TIMESTAMPTZ;
ALTER TABLE public.trips ADD COLUMN end_time_tz   TIMESTAMPTZ;
UPDATE public.trips SET
    start_time_tz = start_time AT TIME ZONE 'UTC',
    end_time_tz   = end_time   AT TIME ZONE 'UTC';
ALTER TABLE public.trips DROP COLUMN start_time;   -- also drops the UNIQUE constraint
ALTER TABLE public.trips DROP COLUMN end_time;
ALTER TABLE public.trips RENAME COLUMN start_time_tz TO start_time;
ALTER TABLE public.trips RENAME COLUMN end_time_tz   TO end_time;
ALTER TABLE public.trips ALTER COLUMN start_time SET NOT NULL;
ALTER TABLE public.trips ALTER COLUMN end_time   SET NOT NULL;
ALTER TABLE public.trips
    ADD CONSTRAINT trips_bike_number_city_id_start_time_key
    UNIQUE (bike_number, city_id, start_time);

COMMIT;
