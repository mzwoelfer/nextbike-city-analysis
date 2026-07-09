# Collection TODO

## Fix trips after timestamp migration

The `migrate_local_time.sql` migration shifted `start_time` / `end_time` in the
trips table +2h, but the `timestamps` JSONB array inside each row was not updated.
This causes old trips to show instant jumps in the visualization instead of
flowing lines.

**Fix: delete all pre-existing trips and reprocess every date from the now-correct bikes data.**

### Step 1 — Find all dates that have bike data

nerdctl exec -i nextbike_postgres psql \
  --username "$(grep ^DB_USER .env | cut -d= -f2)" \
  --dbname   "$(grep ^DB_NAME .env | cut -d= -f2)" \
  --command "SELECT DISTINCT DATE(last_updated) FROM public.bikes WHERE city_id = 467 ORDER BY 1;"

### Step 2 — Delete all trips for the city

nerdctl exec -i nextbike_postgres psql \
  --username "$(grep ^DB_USER .env | cut -d= -f2)" \
  --dbname   "$(grep ^DB_NAME .env | cut -d= -f2)" \
  --command "DELETE FROM public.trips WHERE city_id = 467;"

### Step 3 — Reprocess each date (replace dates with output from Step 1)

for date in 2026-06-01 2026-06-02 ... 2026-07-05; do
  echo "Processing $date..."
  nerdctl run --rm --env-file .env \
    --network nextbike-city-analysis_nextbike_network \
    nextbike-city-analysis-processor \
    --city-id 467 --date "$date"
done



---

# Collection TODO

## Migrate entire database to local-time timestamps

Complete these steps in order. Run all commands from the repo root.

### 1. Stop the collector (no new data during migration)
nerdctl compose -f docker-compose.yaml stop collector

### 2. Run the timestamp migration
nerdctl exec -i nextbike_postgres psql \
  --username "$(grep ^DB_USER .env | cut -d= -f2)" \
  --dbname   "$(grep ^DB_NAME .env | cut -d= -f2)" \
  < collection/migrate_local_time.sql

### 3. Rebuild and restart the collector with the new code
nerdctl compose -f docker-compose.yaml up -d --build collector

### 4. Get the list of all dates with bike data
nerdctl exec -i nextbike_postgres psql \
  --username "$(grep ^DB_USER .env | cut -d= -f2)" \
  --dbname   "$(grep ^DB_NAME .env | cut -d= -f2)" \
  --command "SELECT DISTINCT DATE(last_updated) FROM public.bikes WHERE city_id = 467 ORDER BY 1;"

### 5. Delete all pre-existing trips (they have inconsistent timestamps JSONB)
nerdctl exec -i nextbike_postgres psql \
  --username "$(grep ^DB_USER .env | cut -d= -f2)" \
  --dbname   "$(grep ^DB_NAME .env | cut -d= -f2)" \
  --command "DELETE FROM public.trips WHERE city_id = 467;"

### 6. Reprocess all dates from Step 4
Paste the date list from Step 4 into this loop:

for date in \
  YYYY-MM-DD \
  YYYY-MM-DD; do
  echo "Processing $date..."
  nerdctl run --rm --env-file .env \
    --network nextbike-city-analysis_nextbike_network \
    nextbike-city-analysis-processor \
    --city-id 467 --date "$date"
done


