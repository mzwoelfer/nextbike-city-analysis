import state from "../state.js";

export const apiSource = {
  loadAvailableDates,
  discoverCityNames,
  loadTrips,
  loadStations,
  checkTripExists,
};

/**
 * Load available trip dates from the live API.
 * discoverCityNames() below is a no-op for this source.
 * @returns {Promise<Object<string, string[]>|null>} Dates grouped by city id, or null if unreachable.
 */
async function loadAvailableDates() {
  const response = await fetch("/api/available");
  if (!response.ok) {
    return null;
  }

  const availableRows = await response.json();
  availableRows.forEach(({ city_id: cityId, city_name: cityName }) => {
    state.cities[cityName] = cityId;
  });

  return availableRows.reduce((availableFiles, { city_id: cityId, dates }) => {
    availableFiles[cityId] = dates;
    return availableFiles;
  }, {});
}

/**
 * No-op: the API already supplies city names via loadAvailableDates().
 * Kept so data sources share the same interface.
 * @returns {Promise<Array>} Always empty.
 */
async function discoverCityNames() {
  return [];
}

/**
 * Fetch and normalize trip data for one city/date.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ trips: Object[], timezone: string }>} Trips and timezone.
 */
async function loadTrips(cityId, selectedDate) {
  const response = await fetch(`/api/trips?city_id=${cityId}&date=${selectedDate}`);
  if (!response.ok) {
    throw new Error(`API request failed for trips ${cityId} ${selectedDate}`);
  }

  const geojson = await response.json();
  const timezone = geojson.timezone ?? geojson.features[0]?.properties?.timezone ?? "UTC";
  const trips = geojson.features.map((feature) => normalizeTripFeature(feature, timezone));
  return { trips, timezone };
}

/**
 * Normalize one GeoJSON trip feature into the common trip shape.
 * @param {Object} feature - GeoJSON feature from the API.
 * @param {string} defaultTimezone - Fallback timezone.
 * @returns {Object} Normalized trip.
 */
function normalizeTripFeature(feature, defaultTimezone) {
  return {
    bike_number: feature.properties.bike_number,
    start_time: feature.properties.start_time,
    end_time: feature.properties.end_time,
    duration: feature.properties.duration,
    distance: feature.properties.distance,
    coordinates: feature.geometry.coordinates,
    route_id: feature.properties.route_id ?? null,
    timezone: feature.properties.timezone ?? defaultTimezone ?? "UTC",
  };
}

/**
 * Fetch and normalize station data for one city/date.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ stations: Object[], timezone: string }>} Stations and timezone.
 */
async function loadStations(cityId, selectedDate) {
  const response = await fetch(`/api/stations?city_id=${cityId}&date=${selectedDate}`);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `API request failed for stations ${cityId} ${selectedDate} (status ${response.status}): ${errorText}`,
    );
  }

  const rows = await response.json();
  const timezone = rows[0]?.timezone || state.city_timezone || "UTC";
  const stations = rows.map((row) => normalizeStationRow(row, timezone));
  return { stations, timezone };
}

/**
 * Normalize one API station record into the common station shape.
 * @param {Object} row - Raw station row from the API.
 * @param {string} defaultTimezone - Fallback timezone.
 * @returns {Object} Normalized station.
 */
function normalizeStationRow(row, defaultTimezone) {
  return {
    minute: row.minute,
    id: row.id,
    uid: row.uid,
    latitude: row.latitude,
    longitude: row.longitude,
    name: row.name,
    spot: row.spot,
    station_number: row.station_number,
    maintenance: row.maintenance,
    terminal_type: row.terminal_type,
    city_id: row.city_id,
    city_name: row.city_name,
    bike_count: row.bike_count,
    bike_list: row.bike_list || "",
    timezone: row.timezone || defaultTimezone || "UTC",
  };
}

/**
 * Check trip-data availability from the already-loaded date index - no network call.
 * @param {string|number} cityId - Selected city id.
 * @param {string} date - Date to check.
 * @returns {Promise<boolean>} True when trip data exists for that date.
 */
async function checkTripExists(cityId, date) {
  return state.availableFiles[cityId]?.includes(date) ?? false;
}