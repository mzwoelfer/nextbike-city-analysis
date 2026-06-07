# Test Coverage TODO

Current coverage: 83%. Gaps and actionable fixes below.
Goal: cover every reachable branch with zero or near-zero mocks by extracting pure logic.

---

## utils.py — 73% (Missing: L10-11, 18, 25)

`save_json`, `save_csv`, `save_gzipped_csv` are untested.
All three are pure I/O with no DB dependency.

**Fix:** Add tests in `test_utils.py` using `tempfile.NamedTemporaryFile`.
No mocks, no refactor needed.

- `test_save_json_writes_valid_json` — write dict, reopen file, assert `json.load` roundtrip.
- `test_save_csv_writes_expected_rows` — write DataFrame, reopen with `pd.read_csv`, assert content.
- `test_save_gzipped_csv_is_readable_by_pandas` — write DataFrame, reopen with `pd.read_csv(..., compression="gzip")`, assert content.

---

## trips.py — 80% (Missing: L12-47, 55, 157-177, 216)

### L12-47: `fetch_trip_data` — pandas transformation after SQL

The datetime parsing and duration calculation run after the SQL call.
They are pure DataFrame operations but are unreachable because the SQL call is skipped in tests.

**Refactor:** Extract `_parse_raw_bike_rows(df)` from `fetch_trip_data`:
```python
def _parse_raw_bike_rows(df):
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"]   = pd.to_datetime(df["end_time"])
    df["duration"]   = df["end_time"] - df["start_time"]
    return df
```
`fetch_trip_data` calls `_parse_raw_bike_rows(df)` after the query.

**Tests in `test_trips.py`:**
- `test_parse_raw_bike_rows_calculates_duration` — feed two timestamps, assert `duration` equals their difference.
- `test_parse_raw_bike_rows_preserves_other_columns` — assert non-time columns pass through unchanged.

### L55: `ValueError` branch in `calculate_shortest_path`

```python
if start_node not in G.nodes or end_node not in G.nodes:
    raise ValueError(...)
```

`ox.distance.nearest_nodes` always returns a node that IS in the graph by definition.
This branch is unreachable — dead code (Clean Code G9).

**Fix:** Remove the branch entirely.

### L157-177: uncached route computation path in `process_and_save_trips`

This branch (OSMnx graph download + route loop) requires a live network call.
It is not worth a unit test. Cover it at integration test level only.

**Refactor to improve isolation:** Extract `build_routes_for_pairs(uncached_pairs, G)`:
```python
def build_routes_for_pairs(uncached_pairs, G):
    results = []
    for _, row in uncached_pairs.iterrows():
        distance, segments = calculate_shortest_path(G, ...)
        results.append({...})
    return pd.DataFrame(results)
```
`build_routes_for_pairs` takes a graph object — no DB, no network call inside it.
Pass a synthetic `nx.MultiDiGraph` in tests exactly like `TestCalculateShortestPath` already does.

**Tests in `test_trips.py`:**
- `test_build_routes_for_pairs_returns_expected_columns` — feed two pairs and a synthetic graph, assert output has the six expected columns.
- `test_build_routes_for_pairs_empty_input_returns_empty_dataframe` — feed empty pairs, assert result is an empty DataFrame.

### L216: `export_files` branch in `process_and_save_trips`

The branch is a single `save_gzipped_geojson` call on a built GeoJSON dict.
`save_gzipped_geojson` is already tested. The untested part is the GeoJSON construction.

**Refactor:** Extract `build_trip_geojson(trips)`:
```python
def build_trip_geojson(trips):
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": row["coordinates"]},
            "properties": {
                "bike_number": row["bike_number"],
                "start_time":  row["start_time"],
                "end_time":    row["end_time"],
                "duration":    row["duration"],
                "distance":    row["distance"],
                "timestamps":  row["timestamps"],
            },
        }
        for _, row in trips.iterrows()
    ]
    return {"type": "FeatureCollection", "features": features}
```

**Tests in `test_trips.py`:**
- `test_build_trip_geojson_returns_feature_collection` — assert top-level `type` key.
- `test_build_trip_geojson_feature_count_matches_row_count` — assert `len(features) == len(trips)`.
- `test_build_trip_geojson_properties_match_row` — spot-check one feature's properties against input row.

---

## database.py — 23% (Missing: L10, 26-62, 71-90, 97-118)

All functions mix DB execution with data transformation.
`get_connection` (L10) is untestable without a live DB — skip it.
The transformations inside the other three functions are pure and extractable.

### `fetch_cached_routes` (L26-62)

Contains two pure transforms:
1. Build `pairs_list` from a DataFrame.
2. Parse raw DB rows into a DataFrame, converting `[lon, lat]` to `[lat, lon]`.

**Refactor:** Extract:
```python
def _pairs_to_tuples(unique_pairs):
    return [
        (float(r.start_latitude), float(r.start_longitude),
         float(r.end_latitude),   float(r.end_longitude))
        for _, r in unique_pairs.iterrows()
    ]

def _parse_route_rows(rows):
    df = pd.DataFrame(rows, columns=[
        "start_latitude", "start_longitude", "end_latitude", "end_longitude",
        "distance_meters", "coordinates",
    ])
    df["segments"] = df["coordinates"].apply(
        lambda coords: [[lat, lon] for lon, lat in coords]
    )
    return df.rename(columns={"distance_meters": "distance"})[
        ["start_latitude", "start_longitude", "end_latitude", "end_longitude",
         "distance", "segments"]
    ]
```

**Tests in a new `test_database.py`:**
- `test_pairs_to_tuples_converts_dataframe_rows` — feed a two-row DataFrame, assert list of tuples.
- `test_pairs_to_tuples_empty_input_returns_empty_list` — feed empty DataFrame, assert `[]`.
- `test_parse_route_rows_swaps_lon_lat_to_lat_lon` — feed `[[lon, lat]]` coords, assert segments are `[[lat, lon]]`.
- `test_parse_route_rows_renames_distance_meters_column` — assert output has `distance` not `distance_meters`.

### `insert_routes` (L71-90)

Contains one pure transform: converting `[lat, lon]` segments to `[lon, lat]` for storage.

**Refactor:** Extract:
```python
def _segments_to_geojson_coords(segments):
    return [[lon, lat] for lat, lon in segments]
```

**Tests in `test_database.py`:**
- `test_segments_to_geojson_coords_swaps_lat_lon` — assert `[52.5, 13.4]` becomes `[13.4, 52.5]`.
- `test_segments_to_geojson_coords_empty_input` — assert `[]` in, `[]` out.

### `insert_trips` (L97-118)

No pure transform to extract — all logic is SQL and iteration.
Skip unit test. Cover at integration level only.

---

## cities.py — 25% (Missing: L5-15)

`get_city_coordinates_from_database` is a thin DB wrapper with no extractable logic.

**Refactor:** Accept `conn` as parameter so a caller controls the connection:
```python
def get_city_coordinates_from_database(city_id, conn):
    ...
```
Update all call sites. In production, pass `get_connection()`. In tests, pass a lightweight fake.

Since there is no pure logic to extract, a minimal structural mock of the cursor is acceptable here.

**Test in a new `test_cities.py`:**
- `test_get_city_coordinates_returns_lat_lon_tuple` — pass a fake `conn` whose cursor returns `(52.5, 13.4)`, assert return value is `(52.5, 13.4)`.

---

## Summary: files to create / modify

| Action | File |
|--------|------|
| Add tests | `tests/test_utils.py` |
| Add tests + refactor | `tests/test_trips.py` + `nextbike_processing/trips.py` |
| New file | `tests/test_database.py` |
| New file | `tests/test_cities.py` |
| Refactor | `nextbike_processing/database.py` |
| Refactor | `nextbike_processing/cities.py` |
| Remove dead code | `nextbike_processing/trips.py` L55 |
