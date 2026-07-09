import state from "./state.js";
import { minutesSinceMidnight } from "./utils.js";

/**
 * Parse CSV text into an array of row objects.
 * @param {string} csvText - Raw CSV text.
 * @returns {Promise<Array<Object>>} Parsed rows.
 */
const parseCSV = async (csvText) => {
  const lines = csvText.trim().split("\n");
  const headers = lines[0].split(",");

  // Rawdogging CSV parsing... in the name of personal improvement
  return lines.slice(1).map((line) => {
    const values = [];
    let current = "";
    let insideQuotes = false;

    for (let char of line) {
      if (char === '"' && insideQuotes) {
        insideQuotes = false;
      } else if (char === '"' && !insideQuotes) {
        insideQuotes = true;
      } else if (char === "," && !insideQuotes) {
        values.push(current.trim());
        current = "";
      } else {
        current += char;
      }
    }
    values.push(current.trim());

    return headers.reduce((acc, header, index) => {
      acc[header] = values[index];
      return acc;
    }, {});
  });
};

/**
 * Add city names from API availability rows into shared state.
 * @param {Array<Object>} availableRows - Rows returned by /api/available.
 */
const registerCitiesFromAvailableApi = (availableRows) => {
  availableRows.forEach(({ city_id: cityId, city_name: cityName }) => {
    state.cities[cityName] = cityId;
  });
};

/**
 * Group static station file names by city and date.
 * @param {string[]} fileNames - Station file names.
 * @returns {Object<string, string[]>} Dates grouped by city id.
 */
const groupStationFilesByCityAndDate = (fileNames) => {
  const availableFiles = {};

  fileNames.forEach((fileName) => {
    const match = fileName.match(/(\d+)_stations_(\d{4}-\d{2}-\d{2})\.csv\.gz/);
    if (!match) {
      return;
    }

    const [, cityId, availableDate] = match;
    if (!availableFiles[cityId]) {
      availableFiles[cityId] = [];
    }
    availableFiles[cityId].push(availableDate);
  });

  return availableFiles;
};

/**
 * Load available trip dates from the API.
 * @returns {Promise<Object<string, string[]>|null>} Grouped dates or null.
 */
const loadAvailableDatesFromApi = async () => {
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
};

/**
 * Load available trip dates from manifest.json.
 * @returns {Promise<Object<string, string[]>>} Grouped dates.
 */
const loadAvailableDatesFromManifest = async () => {
  const response = await fetch("data/manifest.json");
  if (!response.ok) {
    throw new Error("Manifest file not found");
  }

  const fileNames = await response.json();
  return groupStationFilesByCityAndDate(fileNames);
};

/**
 * Load available trip dates from the directory listing fallback.
 * @returns {Promise<Object<string, string[]>>} Grouped dates.
 */
const loadAvailableDatesFromDirectoryListing = async () => {
  const response = await fetch("data/");
  const html = await response.text();
  const parser = new DOMParser();
  const documentBody = parser.parseFromString(html, "text/html");
  const fileNames = Array.from(documentBody.querySelectorAll("a"))
    .map((link) => link.getAttribute("href"))
    .filter((fileName) => fileName.endsWith(".csv.gz"));

  return groupStationFilesByCityAndDate(fileNames);
};

/**
 * Load available dates from API or static fallbacks.
 * @returns {Promise<Object<string, string[]>>} Grouped dates by city.
 */
export const loadAvailableFiles = async () => {
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

  try {
    state.useApi = false;
    const availableFiles = await loadAvailableDatesFromManifest();
    console.log("Loaded files from manifest:", availableFiles);
    return availableFiles;
  } catch (err) {
    console.warn(
      "Manifest.json not found or failed to load. Falling back to server-based file fetching:",
      err,
    );

    try {
      const availableFiles = await loadAvailableDatesFromDirectoryListing();
      console.log("Loaded files from server directory:", availableFiles);
      return availableFiles;
    } catch (dirErr) {
      console.error("Failed to fetch directory listing as fallback:", dirErr);
      return {};
    }
  }
};

/**
 * Fetch and parse a gzipped CSV file.
 * @param {string} filePath - Relative path to the .csv.gz file.
 * @returns {Promise<Array<Object>>} Parsed row objects.
 */
const fetchAndParseGzipCSV = async (filePath) => {
  try {
    const response = await fetch(filePath);
    if (!response.ok) throw new Error(`Failed to load ${filePath}`);

    const decompressedStream = response.body.pipeThrough(
      new DecompressionStream("gzip"),
    );
    const text = await new Response(decompressedStream).text();
    const parsedCSV = await parseCSV(text);
    return parsedCSV;
  } catch (err) {
    console.error(`ERROR: Loading CSV file ${filePath}`, err);
    return [];
  }
};

/**
 * Choose the initial city id and date from available files.
 * @param {Object<string, string[]>} availableFiles - Dates grouped by city.
 * @returns {{ cityId: string|number, date: string, hasData: boolean }} Selection result.
 */
const selectInitialCityAndDate = (availableFiles) => {
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
};

/**
 * Load city names from static station exports.
 * @param {string[]} cityIds - Available city ids.
 * @param {string} selectedDate - Date used to read station files.
 * @returns {Promise<void>}
 */
const registerCitiesFromStaticStationFiles = async (cityIds, selectedDate) => {
  const cityRecords = await Promise.all(
    cityIds.map(async (cityId) => {
      const stationRows = await fetchAndParseGzipCSV(
        `data/${cityId}_stations_${selectedDate}.csv.gz`,
      );
      return {
        cityId,
        cityName: stationRows[0]?.city_name,
      };
    }),
  );

  cityRecords.forEach(({ cityId, cityName }) => {
    if (cityName) {
      state.cities[cityName] = cityId;
    }
  });
};

/**
 * Set initial city/date state from the available file index.
 * @returns {Promise<boolean>} True when an initial city/date was selected.
 */
export const loadFirstAvailableData = async () => {
  const { cityId, date, hasData } = selectInitialCityAndDate(state.availableFiles);
  state.city_id = cityId;
  state.date = date;

  if (!hasData) {
    return false;
  }

  if (state.useApi) {
    return true;
  }

  await registerCitiesFromStaticStationFiles(Object.keys(state.availableFiles), state.date);
  return true;
};

/**
 * Create shared trip timing fields for city-local rendering.
 * @param {Object} trip - Normalized trip object.
 * @param {string} timezone - City timezone.
 * @returns {Object} Trip with city-local minute fields.
 */
const attachTripTimingFields = (trip, timezone) => ({
  ...trip,
  start_minute_city: minutesSinceMidnight(new Date(trip.start_time), timezone),
  end_minute_city: minutesSinceMidnight(new Date(trip.end_time), timezone),
});

/**
 * Normalize one API trip feature.
 * @param {Object} feature - GeoJSON feature from the API.
 * @param {string} defaultTimezone - Response timezone fallback.
 * @returns {Object} Normalized trip.
 */
const normalizeApiTripRecord = (feature, defaultTimezone) => ({
  bike_number: feature.properties.bike_number,
  start_time: feature.properties.start_time,
  end_time: feature.properties.end_time,
  duration: feature.properties.duration,
  distance: feature.properties.distance,
  coordinates: feature.geometry.coordinates,
  route_id: feature.properties.route_id ?? null,
  timezone: feature.properties.timezone ?? defaultTimezone ?? "UTC",
});

/**
 * Normalize one static trip CSV row.
 * @param {Object} row - Parsed CSV row.
 * @returns {Object} Normalized trip.
 */
const normalizeStaticTripRecord = (row) => {
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
};

/**
 * Fetch and normalize trip data from the API.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ trips: Object[], timezone: string }>} Trips and city timezone.
 */
const fetchTripsFromApi = async (cityId, selectedDate) => {
  const response = await fetch(`/api/trips?city_id=${cityId}&date=${selectedDate}`);
  if (!response.ok) {
    throw new Error(`API request failed for trips ${cityId} ${selectedDate}`);
  }

  const geojson = await response.json();
  const timezone = geojson.timezone ?? geojson.features[0]?.properties?.timezone ?? "UTC";
  const trips = geojson.features.map((feature) => normalizeApiTripRecord(feature, timezone));
  return { trips, timezone };
};

/**
 * Fetch and normalize trip data from static exports.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ trips: Object[], timezone: string }>} Trips and city timezone.
 */
const fetchTripsFromStatic = async (cityId, selectedDate) => {
  const rows = await fetchAndParseGzipCSV(`data/${cityId}_trips_${selectedDate}.csv.gz`);
  if (!rows.length) {
    throw new Error(`No trip data for city ${cityId} on ${selectedDate}`);
  }

  const trips = rows.map(normalizeStaticTripRecord);
  const timezone = trips[0]?.timezone || "UTC";
  return { trips, timezone };
};

/**
 * Save normalized trip data into shared state.
 * @param {Object[]} trips - Normalized trips.
 * @param {string} timezone - City timezone.
 */
const applyTripsToState = (trips, timezone) => {
  state.city_timezone = timezone;
  state.tripsData = trips.map((trip) => attachTripTimingFields(trip, trip.timezone || timezone));

  if (state.tripsData.length > 0) {
    state.city_lat = state.tripsData[0].coordinates[0][1];
    state.city_lng = state.tripsData[0].coordinates[0][0];
  }
};

/**
 * Load trip data for the current city and date into shared state.
 * @returns {Promise<void>}
 */
export const loadTripsData = async () => {
  try {
    const { trips, timezone } = state.useApi
      ? await fetchTripsFromApi(state.city_id, state.date)
      : await fetchTripsFromStatic(state.city_id, state.date);

    applyTripsToState(trips, timezone);
    console.log("Trips data loaded:", state.tripsData);
  } catch (err) {
    console.error("Error loading trip data:", err);
  }
};

/**
 * Create shared station timing fields for city-local rendering.
 * @param {Object} station - Normalized station object.
 * @param {string} timezone - City timezone.
 * @returns {Object} Station with city-local minute field.
 */
const attachStationTimingFields = (station, timezone) => ({
  ...station,
  minute_city: minutesSinceMidnight(new Date(station.minute), timezone),
});

/**
 * Normalize one API station record.
 * @param {Object} row - Raw station row from the API.
 * @param {string} defaultTimezone - City timezone fallback.
 * @returns {Object} Normalized station.
 */
const normalizeApiStationRecord = (row, defaultTimezone) => ({
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
});

/**
 * Normalize one static station row.
 * @param {Object} row - Parsed CSV row.
 * @param {string} defaultTimezone - City timezone fallback.
 * @returns {Object} Normalized station.
 */
const normalizeStaticStationRecord = (row, defaultTimezone) => ({
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
});

/**
 * Fetch and normalize station data from the API.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ stations: Object[], timezone: string }>} Stations and city timezone.
 */
const fetchStationsFromApi = async (cityId, selectedDate) => {
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
};

/**
 * Fetch and normalize station data from static exports.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<{ stations: Object[], timezone: string }>} Stations and city timezone.
 */
const fetchStationsFromStatic = async (cityId, selectedDate) => {
  const rows = await fetchAndParseGzipCSV(`data/${cityId}_stations_${selectedDate}.csv.gz`);
  const timezone = rows[0]?.timezone || state.city_timezone || "UTC";
  const stations = rows.map((row) => normalizeStaticStationRecord(row, timezone));
  return { stations, timezone };
};

/**
 * Save normalized station data into shared state.
 * @param {Object[]} stations - Normalized stations.
 * @param {string} timezone - City timezone.
 */
const applyStationsToState = (stations, timezone) => {
  state.city_timezone = timezone || state.city_timezone || "UTC";
  state.stationData = stations.map((station) =>
    attachStationTimingFields(station, station.timezone || state.city_timezone),
  );
};

/**
 * Load station data for the current city and date into shared state.
 * @returns {Promise<void>}
 */
export const loadStationData = async () => {
  try {
    const { stations, timezone } = state.useApi
      ? await fetchStationsFromApi(state.city_id, state.date)
      : await fetchStationsFromStatic(state.city_id, state.date);

    applyStationsToState(stations, timezone);
    console.log("Station data loaded:", state.stationData);
  } catch (err) {
    console.error("Error loading station data:", err);
  }
};

/**
 * Check whether trip data exists for a given date.
 * @param {string} date - Date to check.
 * @returns {Promise<boolean>} True when trip data exists.
 */
export const checkTripsDataExists = async (date) => {
  if (state.useApi) {
    return state.availableFiles[state.city_id]?.includes(date) ?? false;
  }
  try {
    const response = await fetch(
      `data/${state.city_id}_trips_${date}.geojson.gz`,
      { method: "HEAD" },
    );
    return response.ok;
  } catch (err) {
    console.error("Error checking trip data file:", err);
    return false;
  }
};
