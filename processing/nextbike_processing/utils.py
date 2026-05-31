import gzip
import os
import json


def save_json(file_path, data):
    """
    Save JSON data to configured path
    """
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def save_csv(file_path, df):
    """
    Save Dataframe to CSV file
    """
    df.to_csv(file_path, index=False)


def save_gzipped_csv(file_path, df):
    """
    Save Dataframe to gzipped CSV file
    """
    df.to_csv(file_path, index=False, compression="gzip")


def save_gzipped_geojson(file_path, data):
    """
    Save a GeoJSON-serialisable dict to a gzipped file
    """
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        json.dump(data, f)


def ensure_directory_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
