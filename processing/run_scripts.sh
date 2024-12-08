#!/bin/bash

if [ $# -ne 4 ] || [ "$1" != "--export-folder" ] || [ "$3" != "--city-id" ]; then
  echo "Usage: $0 --export-folder <export_folder_path> --city-id <city_id>"
  exit 1
fi

EXPORT_FOLDER=$2
CITY_ID=$4

echo "Running pull_stations.py with --export-folder $EXPORT_FOLDER and --city-id $CITY_ID"
python pull_stations.py --export-folder "$EXPORT_FOLDER" --city-id "$CITY_ID"

if [ $? -ne 0 ]; then
  echo "Error while running pull_stations.py"
  exit 1
fi

echo "Running calculate_trips.py with --export-folder $EXPORT_FOLDER and --city-id $CITY_ID"
python calculate_trips.py --export-folder "$EXPORT_FOLDER" --city-id "$CITY_ID"

if [ $? -ne 0 ]; then
  echo "Error while running calculate_trips.py"
  exit 1
fi

echo "Both scripts executed successfully."


