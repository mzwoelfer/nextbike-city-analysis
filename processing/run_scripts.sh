#!/bin/bash

if [ $# -ne 2 ] || [ "$1" != "--export-folder" ]; then
  echo "Usage: $0 --export-folder <export_folder_path>"
  exit 1
fi

EXPORT_FOLDER=$2

echo "Running pull_stations.py with --export-folder $EXPORT_FOLDER"
python pull_stations.py --export-folder "$EXPORT_FOLDER"

if [ $? -ne 0 ]; then
  echo "Error while running pull_stations.py"
  exit 1
fi

echo "Running calculate_trips.py with --export-folder $EXPORT_FOLDER"
python calculate_trips.py --export-folder "$EXPORT_FOLDER"

if [ $? -ne 0 ]; then
  echo "Error while running calculate_trips.py"
  exit 1
fi

echo "Both scripts executed successfully."

