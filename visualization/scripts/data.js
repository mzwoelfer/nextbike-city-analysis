import state from "./state.js";
import {
  checkStaticTripDataExists,
  loadAvailableDatesFromDirectoryListing,
  loadAvailableDatesFromManifest,
  loadStaticCityRecords,
  loadStaticStationRows,
  loadStaticTripRows,
} from "./staticFiles.js";
import { minutesSinceMidnight } from "./utils.js";

/**
 * Load available dates from the API first, then fall back to static files.
 * @returns {Promise<Object<string, string[]>>} Dates grouped by city id.
 */
export async function loadAvailableFiles() {
  try {
    const availableFiles = await loadAvailableDatesFromApi();
    if (availableFiles) {
      state.useApi = true;
      console.log("Loaded available data from API:", availableFiles);
      return availableFiles;
    }
  } catch (err) {
    console.warn("API failed, falling back to static:", err);
  }

  state.useApi = false;

  try {
    const availableFiles = await loadAvailableDatesFromManifest();
    console.log("Loaded files from manifest:", availableFiles);
    return availableFiles;
  } catch (err) {
    console.warn(
      "Manifest.json not found or failed to load. Falling back to server-based file fetching:",
      err,
    );
  }

  try {
    const availableFiles = await loadAvailableDatesFromDirectoryListing();
    console.log("Loaded files from server directory:", availableFiles);
    return availableFiles;
  } catch (err) {
    console.error("Failed to fetch directory listing as fallback:", err);
    return {};
  }
}

/**
 * Load available trip dates from the API.
 * @returns {Promise<Object<string, string[]>|null>} Grouped dates or null when the API is unavailable.
 */
async function loadAvailableDatesFromApi() {
  const response = await fetch("/api/available");
  if (!response.ok) {
    return null;
  }

  const availableRows = await response.json();
  registerCitiesFromAvailableApi(availableRows);

  return availableRows.reduce((availableFiles, { city_id: cityId, dates }) => {
    availableFiles[cityId] = dates;
    return availableFiles;
  }, {});
}

/**
 * Register city names returned by the availability API.
 * @param {Array<Object>} availableRows - Rows returned by /api/available.
 */
function registerCitiesFromAvailableApi(availableRows) {
  availableRows.forEach(({ city_id: cityId, city_name: cityName }) => {
    state.cities[cityName] = cityId;
  });
}

/**
 * Set the initial city and date based on the available file index.
 * @returns {Promise<boolean>} True when a usable city/date selection exists.
 */
export async function loadFirstAvailableData() {
  const initialSelection = selectInitialCityAndDate(state.availableFiles);
  state.city_id = initialSelection.cityId;
  state.date = initialSelection.date;

  if (!initialSelection.hasData) {
    return false;
  }

  if (state.useApi) {
    return true;
  }

  await registerCitiesFromStaticStationFiles(
    Object.keys(state.availableFiles),
    state.date,
  );
  return true;
}

/**
 * Choose the first city and date from the available file index.
 * @param {Object<string, string[]>} availableFiles - Dates grouped by city id.
 * @returns {{ cityId: string|number, date: string, hasData: boolean }} Initial selection.
 */
function selectInitialCityAndDate(availableFiles) {
  const cityIds = Object.keys(availableFiles);
  if (!cityIds.length) {
    return { cityId: 0, date: "", hasData: false };
  }

  const firstCityId = cityIds[0];
  const firstCityDates = availableFiles[firstCityId] || [];
  if (!firstCityDates.length) {
    return { cityId: Number(firstCityId), date: "", hasData: false };
  }

  return {
    cityId: firstCityId,
    date: firstCityDates[0],
    hasData: true,
  };
}

/**
 * Register city names from static station files.
 * @param {string[]} cityIds - Available city ids.
 * @param {string} selectedDate - Date used to load static station files.
 * @returns {Promise<void>}
 */
async function registerCitiesFromStaticStationFiles(cityIds, selectedDate) {
  const cityRecords = await loadStaticCityRecords(cityIds, selectedDate);

  cityRecords.forEach(({ cityId, cityName }) => {
    if (cityName) {
      state.cities[cityName] = cityId;
    }
  });
}

/**
 * Load trip data for the current city and date.
 * @returns {Promise<void>}
 */
export async function loadTripsData() {
  try {
    const tripDataset = state.useApi
      ? await fetchTripsFromApi(state.city_id, state.date)
      : await fetchTripsFromStatic(state.city_id, state.date);

    applyTripsToState(tripDataset.trips, tripDataset.timezone);
    console.log("Trips data loaded:", state.tripsData);
  } catch (err) {
    console.error("Error loading trip data:", err);
  }
}

/**
 * Fetch and normalize trip data from the API.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ trips: Object[], timezone: string }>} Trips and timezone.
 */
async function fetchTripsFromApi(cityId, selectedDate) {
  const response = await fetch(`/api/trips?city_id=${cityId}&date=${selectedDate}`);
  if (!response.ok) {
    throw new Error(`API request failed for trips ${cityId} ${selectedDate}`);
  }

  const geojson = await response.json();
  const timezone = geojson.timezone ?? geojson.features[0]?.properties?.timezone ?? "UTC";
  const trips = geojson.features.map((feature) => normalizeApiTripRecord(feature, timezone));
  return { trips, timezone };
}

/**
 * Fetch and normalize trip data from static CSV exports.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ trips: Object[], timezone: string }>} Trips and timezone.
 */
async function fetchTripsFromStatic(cityId, selectedDate) {
  const rows = await loadStaticTripRows(cityId, selectedDate);
  if (!rows.length) {
    throw new Error(`No trip data for city ${cityId} on ${selectedDate}`);
  }

  const trips = rows.map(normalizeStaticTripRecord);
  const timezone = trips[0]?.timezone || "UTC";
  return { trips, timezone };
}

/**
 * Save normalized trips into shared state.
 * @param {Object[]} trips - Normalized trips.
 * @param {string} timezone - City timezone.
 */
function applyTripsToState(trips, timezone) {
  state.city_timezone = timezone;
  state.tripsData = trips.map((trip) =>
    attachTripTimingFields(trip, trip.timezone || timezone),
  );

  if (state.tripsData.length > 0) {
    state.city_lat = state.tripsData[0].coordinates[0][1];
    state.city_lng = state.tripsData[0].coordinates[0][0];
  }
}

/**
 * Normalize one API trip feature.
 * @param {Object} feature - GeoJSON feature from the API.
 * @param {string} defaultTimezone - Fallback timezone.
 * @returns {Object} Normalized trip.
 */
function normalizeApiTripRecord(feature, defaultTimezone) {
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
 * Normalize one static trip CSV row.
 * @param {Object} row - Parsed CSV row.
 * @returns {Object} Normalized trip.
 */
function normalizeStaticTripRecord(row) {
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
 * Attach city-local minute fields to a trip.
 * @param {Object} trip - Normalized trip.
 * @param {string} timezone - City timezone.
 * @returns {Object} Trip with derived timing fields.
 */
function attachTripTimingFields(trip, timezone) {
  return {
    ...trip,
    start_minute_city: minutesSinceMidnight(new Date(trip.start_time), timezone),
    end_minute_city: minutesSinceMidnight(new Date(trip.end_time), timezone),
  };
}

/**
 * Load station data for the current city and date.
 * @returns {Promise<void>}
 */
export async function loadStationData() {
  try {
    const stationDataset = state.useApi
      ? await fetchStationsFromApi(state.city_id, state.date)
      : await fetchStationsFromStatic(state.city_id, state.date);

    applyStationsToState(stationDataset.stations, stationDataset.timezone);
    console.log("Station data loaded:", state.stationData);
  } catch (err) {
    console.error("Error loading station data:", err);
  }
}

/**
 * Fetch and normalize station data from the API.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ stations: Object[], timezone: string }>} Stations and timezone.
 */
async function fetchStationsFromApi(cityId, selectedDate) {
  const response = await fetch(`/api/stations?city_id=${cityId}&date=${selectedDate}`);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `API request failed for stations ${cityId} ${selectedDate} (status ${response.status}): ${errorText}`,
    );
  }

  const rows = await response.json();
  const timezone = rows[0]?.timezone || state.city_timezone || "UTC";
  const stations = rows.map((row) => normalizeApiStationRecord(row, timezone));
  return { stations, timezone };
}

/**
 * Fetch and normalize station data from static CSV exports.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ stations: Object[], timezone: string }>} Stations and timezone.
 */
async function fetchStationsFromStatic(cityId, selectedDate) {
  const rows = await loadStaticStationRows(cityId, selectedDate);
  const timezone = rows[0]?.timezone || state.city_timezone || "UTC";
  const stations = rows.map((row) => normalizeStaticStationRecord(row, timezone));
  return { stations, timezone };
}

/**
 * Save normalized stations into shared state.
 * @param {Object[]} stations - Normalized stations.
 * @param {string} timezone - City timezone.
 */
function applyStationsToState(stations, timezone) {
  state.city_timezone = timezone || state.city_timezone || "UTC";
  state.stationData = stations.map((station) =>
    attachStationTimingFields(station, station.timezone || state.city_timezone),
  );
}

/**
 * Normalize one API station record.
 * @param {Object} row - Raw station row from the API.
 * @param {string} defaultTimezone - Fallback timezone.
 * @returns {Object} Normalized station.
 */
function normalizeApiStationRecord(row, defaultTimezone) {
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
 * Normalize one static station CSV row.
 * @param {Object} row - Parsed CSV row.
 * @param {string} defaultTimezone - Fallback timezone.
 * @returns {Object} Normalized station.
 */
function normalizeStaticStationRecord(row, defaultTimezone) {
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
 * Attach city-local minute fields to a station row.
 * @param {Object} station - Normalized station row.
 * @param {string} timezone - City timezone.
 * @returns {Object} Station with derived timing fields.
 */
function attachStationTimingFields(station, timezone) {
  return {
    ...station,
    minute_city: minutesSinceMidnight(new Date(station.minute), timezone),
  };
}

/**
 * Check whether trip data exists for a date.
 * @param {string} date - Date to check.
 * @returns {Promise<boolean>} True when trip data exists.
 */
export async function checkTripsDataExists(date) {
  if (state.useApi) {
    return state.availableFiles[state.city_id]?.includes(date) ?? false;
  }

  try {
    return await checkStaticTripDataExists(state.city_id, date);
  } catch (err) {
    console.error("Error checking trip data file:", err);
    return false;
  }
}
