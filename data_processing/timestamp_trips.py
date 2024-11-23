from datetime import datetime, timedelta
import json
import os

def add_timestamps_to_segments(trips):
    """
    Adds timestamps to each segment in the trip data.
    """
    for trip in trips:
        start_time = datetime.fromisoformat(trip["start_time"])
        end_time = datetime.fromisoformat(trip["end_time"])

        total_duration = (end_time - start_time).total_seconds()

        num_segments = len(trip["segments"])
        time_increment = total_duration / max(num_segments - 1, 1)  # Avoid division by zero

        for i, segment in enumerate(trip["segments"]):
            timestamp = start_time + timedelta(seconds=i * time_increment)
            segment.append(timestamp.isoformat())  # Append timestamp to the segment

    return trips

def process_files(input_dir, output_dir):
    """
    Processes all JSON files in the input directory, adds timestamps to their segments,
    and saves them with the prefix "timestamped_" in the output directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_name in os.listdir(input_dir):
        if file_name.endswith(".json"):
            input_path = os.path.join(input_dir, file_name)
            output_path = os.path.join(output_dir, f"timestamped_{file_name}")

            with open(input_path, "r") as f:
                trips = json.load(f)

            updated_trips = add_timestamps_to_segments(trips)

            with open(output_path, "w") as f:
                json.dump(updated_trips, f, indent=4)

            print(f"Processed {file_name} -> {output_path}")

input_directory = "data"
output_directory = "data"

process_files(input_directory, output_directory)
