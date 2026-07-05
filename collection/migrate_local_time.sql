-- One-time migration: convert existing UTC-naive timestamps to local city time.
--
-- The existing data was collected in containers running UTC, so all TIMESTAMP WITHOUT TIME ZONE
-- values are actually UTC. This script annotates them as UTC and converts to each city's
-- local timezone (sourced from the cities table itself).
--
-- Run BEFORE restarting the collector with the updated code:
--   psql -h localhost -p 5432 -U <user> -d <dbname> -f migrate_local_time.sql

BEGIN;

UPDATE public.bikes b
SET last_updated = (b.last_updated AT TIME ZONE 'UTC') AT TIME ZONE c.timezone
FROM public.cities c
WHERE b.city_id = c.city_id;

UPDATE public.stations s
SET last_updated = (s.last_updated AT TIME ZONE 'UTC') AT TIME ZONE c.timezone
FROM public.cities c
WHERE s.city_id = c.city_id;

-- cities table references its own timezone column
UPDATE public.cities
SET last_updated = (last_updated AT TIME ZONE 'UTC') AT TIME ZONE timezone;

UPDATE public.trips t
SET start_time = (t.start_time AT TIME ZONE 'UTC') AT TIME ZONE c.timezone,
    end_time   = (t.end_time   AT TIME ZONE 'UTC') AT TIME ZONE c.timezone
FROM public.cities c
WHERE t.city_id = c.city_id;

COMMIT;
