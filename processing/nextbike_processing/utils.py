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


def ensure_directory_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
