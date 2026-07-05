BEGIN;

ALTER TABLE public.trips DROP COLUMN timestamps;

COMMIT;
-- INSERT INTO public.schema_migrations (version, description, reason)
-- VALUES ('003', 'Drop timestamps JSONB from trips',
--   'timestamps was synthetic interpolated data computed only for the visualization animator.
--    Replaced with fraction-based interpolation in trips.js using start_time/end_time/coordinates.');