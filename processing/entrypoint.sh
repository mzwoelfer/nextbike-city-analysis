#!/bin/bash
set -e

# If arguments are provided, run them directly (manual execution)
if [ $# -gt 0 ]; then
    exec python -m nextbike_processing.main "$@"
fi

# Otherwise, run the scheduled loop
while true; do
  sleep_seconds=$(( $(date -d 'tomorrow 00:00' +%s) - $(date +%s) ))
  echo "Next auto-processing at midnight in $sleep_seconds seconds"
  sleep "$sleep_seconds"
  
  YESTERDAY=$(date -d 'yesterday' +%Y-%m-%d)
  echo "Running scheduled processing for $YESTERDAY"
  
  for city_id in $(echo "$CITY_IDS" | tr ',' ' '); do
    echo "Processing city $city_id for $YESTERDAY"
    python -m nextbike_processing.main --city-id "$city_id" --date "$YESTERDAY"
  done
done
