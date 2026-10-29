const CSV_HEADERS = [
  "city_id",
  "city_name",
  "bike_number",
  "start_time",
  "end_time",
  "duration_seconds",
  "distance_meters",
  "route_id",
  "start_latitude",
  "start_longitude",
  "end_latitude",
  "end_longitude",
  "timezone",
];

export function buildMonthlyTripsCsv(trips, cityId, cityName) {
  const rows = trips.map((trip) => {
    const start = trip.coordinates?.[0];
    const end = trip.coordinates?.at(-1);
    return [
      cityId,
      cityName,
      trip.bike_number,
      trip.start_time,
      trip.end_time,
      trip.duration,
      trip.route_id == null ? "" : trip.distance,
      trip.route_id,
      start?.[1],
      start?.[0],
      end?.[1],
      end?.[0],
      trip.timezone,
    ];
  });

  return [CSV_HEADERS, ...rows]
    .map((row) => row.map(escapeCsvValue).join(","))
    .join("\r\n");
}

function escapeCsvValue(value) {
  const text = value == null ? "" : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}