import { fetchAndParseGzipCsv } from "../csvParser.js";

export const staticSource = {
  loadAvailableDates,
  discoverCityNames,
  loadTrips,
  loadStations,
  checkTripExists,
};

/**
 * Discover available trip dates for the static demo.
 * Tries the pre-built manifest first (this is what GitHub Pages serves).
 * Falls back to a directory listing, which only works when the file server
 * exposes one - useful for local dev servers, not GitHub Pages.
 * @returns {Promise<Object<string, string[]>>} Dates grouped by city id.
 */
async function loadAvailableDates() {
  try {
    return await loadDatesFromManifest();
  } catch (err) {
    console.warn("manifest.json unavailable. Falling back to directory listing.", err);
    return loadDatesFromDirectoryListing();
  }
}

/**
 * Load available trip dates from manifest.json.
 * @returns {Promise<Object<string, string[]>>} Grouped dates.
 */
async function loadDatesFromManifest() {
  const response = await fetch("data/manifest.json");
  if (!response.ok) {
    throw new Error("Manifest file not found");
  }

  const fileNames = await response.json();
  return groupStationFilesByCityAndDate(fileNames);
}

/**
 * Load available trip dates from a server directory listing.
 * @returns {Promise<Object<string, string[]>>} Grouped dates.
 */
async function loadDatesFromDirectoryListing() {
  const response = await fetch("data/");
  const html = await response.text();
  const parsedHtml = new DOMParser().parseFromString(html, "text/html");
  const fileNames = Array.from(parsedHtml.querySelectorAll("a"))
    .map((link) => link.getAttribute("href"))
    .filter((fileName) => fileName.endsWith(".csv.gz"));

  return groupStationFilesByCityAndDate(fileNames);
}

/**
 * Group static station file names by city and date.
 * @param {string[]} fileNames - Station file names.
 * @returns {Object<string, string[]>} Dates grouped by city id.
 */
function groupStationFilesByCityAndDate(fileNames) {
  const availableFiles = {};

  fileNames.forEach((fileName) => {
    const match = fileName.match(/(\d+)_stations_(\d{4}-\d{2}-\d{2})\.csv\.gz/);
    if (!match) return;

    const [, cityId, availableDate] = match;
    if (!availableFiles[cityId]) {
      availableFiles[cityId] = [];
    }
    availableFiles[cityId].push(availableDate);
  });

  return availableFiles;
}

/**
 * Read city display names out of each city's station export for one date.
 * The static manifest carries only ids and dates, not names.
 * @param {string[]} cityIds - Available city ids.
 * @param {string} selectedDate - Date used to read station files.
 * @returns {Promise<Array<{ cityId: string, cityName: string|undefined }>>} Discovered names.
 */
async function discoverCityNames(cityIds, selectedDate) {
  return Promise.all(
    cityIds.map(async (cityId) => {
      const stationRows = await fetchAndParseGzipCsv(`data/${cityId}_stations_${selectedDate}.csv.gz`);
      return { cityId, cityName: stationRows[0]?.city_name };
    }),
  );
}

/**
 * Fetch and normalize trip data for one city/date from the static export.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ trips: Object[], timezone: string }>} Trips and timezone.
 */
async function loadTrips(cityId, selectedDate) {
  const rows = await fetchAndParseGzipCsv(`data/${cityId}_trips_${selectedDate}.csv.gz`);
  if (!rows.length) {
    throw new Error(`No trip data for city ${cityId} on ${selectedDate}`);
  }

  const trips = rows.map(normalizeTripRow);
  const timezone = trips[0]?.timezone || "UTC";
  return { trips, timezone };
}

/**
 * Normalize one static trip CSV row into the common trip shape.
 * @param {Object} row - Parsed CSV row.
 * @returns {Object} Normalized trip.
 */
function normalizeTripRow(row) {
  const segments = JSON.parse(row.segments.replace(/'/g, '"'));
  return {
    bike_number: row.bike_number,
    start_time: row.start_time,
    end_time: row.end_time,
    duration: Number(row.duration),
    distance: Number(row.distance),
    coordinates: segments.map(([lat, lon]) => [lon, lat]),
    route_id: row.route_id != null ? Number(row.route_id) : null,
    timezone: row.timezone || "UTC",
  };
}

/**
 * Fetch and normalize station data for one city/date from the static export.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ stations: Object[], timezone: string }>} Stations and timezone.
 */
async function loadStations(cityId, selectedDate) {
  const rows = await fetchAndParseGzipCsv(`data/${cityId}_stations_${selectedDate}.csv.gz`);
  const timezone = rows[0]?.timezone || "UTC";
  const stations = rows.map((row) => normalizeStationRow(row, timezone));
  return { stations, timezone };
}

/**
 * Normalize one static station CSV row into the common station shape.
 * @param {Object} row - Parsed CSV row.
 * @param {string} defaultTimezone - Fallback timezone.
 * @returns {Object} Normalized station.
 */
function normalizeStationRow(row, defaultTimezone) {
  return {
    minute: row.minute,
    id: Number(row.id),
    uid: Number(row.uid),
    latitude: Number(row.latitude),
    longitude: Number(row.longitude),
    name: row.name,
    spot: row.spot === "True",
    station_number: Number(row.station_number),
    maintenance: row.maintenance === "True",
    terminal_type: row.terminal_type,
    city_id: Number(row.city_id),
    city_name: row.city_name,
    bike_count: Number(row.bike_count),
    bike_list: row.bike_list || "",
    timezone: row.timezone || defaultTimezone || "UTC",
  };
}

/**
 * Check whether static trip data exists for a date.
 * NOTE: checks for a `.geojson.gz` file, but loadTrips() above reads a
 * `.csv.gz` file - this mismatch exists in the current export naming and
 * is carried over unchanged here. Flagging it; not silently "fixed".
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Date to check.
 * @returns {Promise<boolean>} True when the trip file exists.
 */
async function checkTripExists(cityId, selectedDate) {
  const response = await fetch(
    `data/${cityId}_trips_${selectedDate}.geojson.gz`,
    { method: "HEAD" },
  );
  return response.ok;
}