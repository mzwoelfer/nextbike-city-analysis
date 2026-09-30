import gzip
import json
import os
import tempfile
import unittest

import pandas as pd

from nextbike_processing.utils import (
    ensure_directory_exists,
    save_csv,
    save_gzipped_csv,
    save_gzipped_geojson,
    save_json,
)


class TestFileWriters(unittest.TestCase):
    def test_save_json_roundtrip(self):
        data = {"city_id": 467, "dates": ["2026-06-08"]}
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.json")
            save_json(path, data)

            with open(path, encoding="utf-8") as file:
                self.assertEqual(json.load(file), data)

    def test_save_csv_roundtrip(self):
        data = pd.DataFrame({"city_id": [467], "city_name": ["Gießen"]})
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.csv")
            save_csv(path, data)

            pd.testing.assert_frame_equal(pd.read_csv(path), data)

    def test_save_gzipped_csv_roundtrip(self):
        data = pd.DataFrame({"city_id": [467], "bike_count": [12]})
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.csv.gz")
            save_gzipped_csv(path, data)

            pd.testing.assert_frame_equal(pd.read_csv(path, compression="gzip"), data)


class TestSaveGzippedGeojson(unittest.TestCase):
    def test_roundtrip_empty_feature_collection(self):
        data = {"type": "FeatureCollection", "features": []}
        with tempfile.NamedTemporaryFile(suffix=".geojson.gz", delete=False) as f:
            path = f.name
        try:
            save_gzipped_geojson(path, data)
            with gzip.open(path, "rt", encoding="utf-8") as f:
                result = json.load(f)
            self.assertEqual(result, data)
        finally:
            os.unlink(path)

    def test_coordinates_and_properties_preserved(self):
        data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[13.4, 52.5], [13.5, 52.6]],
                },
                "properties": {
                    "bike_number": "42",
                    "duration": 780,
                    "timestamps": ["2026-05-30T08:00:00", "2026-05-30T08:13:00"],
                },
            }],
        }
        with tempfile.NamedTemporaryFile(suffix=".geojson.gz", delete=False) as f:
            path = f.name
        try:
            save_gzipped_geojson(path, data)
            with gzip.open(path, "rt", encoding="utf-8") as f:
                result = json.load(f)
            feature = result["features"][0]
            self.assertEqual(feature["geometry"]["coordinates"], [[13.4, 52.5], [13.5, 52.6]])
            self.assertEqual(feature["properties"]["bike_number"], "42")
            self.assertEqual(feature["properties"]["timestamps"], ["2026-05-30T08:00:00", "2026-05-30T08:13:00"])
        finally:
            os.unlink(path)

    def test_output_is_gzip_compressed(self):
        """File must be readable as gzip — not plain JSON."""
        data = {"type": "FeatureCollection", "features": []}
        with tempfile.NamedTemporaryFile(suffix=".geojson.gz", delete=False) as f:
            path = f.name
        try:
            save_gzipped_geojson(path, data)
            with open(path, "rb") as f:
                magic = f.read(2)
            # Gzip magic bytes
            self.assertEqual(magic, b"\x1f\x8b")
        finally:
            os.unlink(path)


class TestEnsureDirectoryExists(unittest.TestCase):
    def test_creates_new_directory(self):
        with tempfile.TemporaryDirectory() as parent:
            new_dir = os.path.join(parent, "new_subdir")
            self.assertFalse(os.path.exists(new_dir))
            ensure_directory_exists(new_dir)
            self.assertTrue(os.path.isdir(new_dir))

    def test_creates_nested_directories(self):
        with tempfile.TemporaryDirectory() as parent:
            nested = os.path.join(parent, "a", "b", "c")
            ensure_directory_exists(nested)
            self.assertTrue(os.path.isdir(nested))

    def test_does_not_raise_if_directory_already_exists(self):
        with tempfile.TemporaryDirectory() as existing:
            try:
                ensure_directory_exists(existing)
            except Exception as e:
                self.fail(f"ensure_directory_exists raised unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main()
