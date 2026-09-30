#!/bin/bash
set -e

# If arguments are provided, run them directly (manual execution)
if [ $# -gt 0 ]; then
    exec python -m nextbike_processing.main "$@"
fi

# Otherwise, run the scheduled loop.
# TEST_RUN_SECONDS=1 shortens the wait so the midnight path can be verified quickly.
while true; do
  if [ -n "${TEST_RUN_SECONDS:-}" ]; then
    sleep_seconds="$TEST_RUN_SECONDS"
    process_date=$(date -d 'today' +%Y-%m-%d)
    echo "Test mode enabled. Running scheduled processing for $process_date in $sleep_seconds seconds"
  else
    sleep_seconds=$(( $(date -d 'tomorrow 00:00' +%s) - $(date +%s) ))
    echo "Next auto-processing at midnight in $sleep_seconds seconds"
  fi

  sleep "$sleep_seconds"

  if [ -z "${TEST_RUN_SECONDS:-}" ]; then
    process_date=$(date -d 'yesterday' +%Y-%m-%d)
  fi

  echo "Running scheduled processing for $process_date"

  for city_id in $(echo "$CITY_IDS" | tr ',' ' '); do
    echo "Processing city $city_id for $process_date"
    python -m nextbike_processing.main --city-id "$city_id" --date "$process_date"
  done
done
