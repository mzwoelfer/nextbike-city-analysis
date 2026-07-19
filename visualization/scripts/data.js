import state from "./state.js";
import { apiSource } from "./dataSources/apiSource.js";
import { staticSource } from "./dataSources/staticSource.js";
import { minutesSinceMidnight } from "./utils.js";

let _dataSource = null;

/**
 * Picks data source for the session: 
 * the live API if reachable,
 * otherwise the static CSV export bundled for the GitHub Pages demo.
 * @returns {Promise<Object<string, string[]>>} Dates grouped by city id.
 */
export async function loadAvailableFiles() {
  try {
    const availableFiles = await apiSource.loadAvailableDates();
    if (availableFiles) {
      _dataSource = apiSource;
      console.log("Data source: live API.", availableFiles);
      return availableFiles;
    }
  } catch (err) {
    console.warn("Live API unreachable. Falling back to static CSV export.", err);
  }

  _dataSource = staticSource;
  const availableFiles = await staticSource.loadAvailableDates();
  console.log("Data source: static CSV export.", availableFiles);
  return availableFiles;
}

/**
 * Set the initial city and date, then register city display names.
 * @returns {Promise<boolean>} True when a usable city/date selection exists.
 */
export async function loadFirstAvailableData() {
  const initialSelection = selectInitialCityAndDate(state.availableFiles);
  state.city_id = initialSelection.cityId;
  state.date = initialSelection.date;

  if (!initialSelection.hasData) {
    return false;
  }

  const cityNames = await _dataSource.discoverCityNames(
    Object.keys(state.availableFiles),
    state.date,
  );
  cityNames.forEach(({ cityId, cityName }) => {
    if (cityName) state.cities[cityName] = cityId;
  });

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
 * Load trip data for the current city and date via the selected source.
 * @returns {Promise<void>}
 */
export async function loadTripsData() {
  try {
    const { trips, timezone } = await _dataSource.loadTrips(state.city_id, state.date);
    applyTripsToState(trips, timezone);
    console.log("Trips data loaded:", state.tripsData);
  } catch (err) {
    console.error("Error loading trip data:", err);
  }
}

/**
 * Save normalized trips into state, attaching timing fields.
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
 * Load station data for the current city and date via the selected source.
 * @returns {Promise<void>}
 */
export async function loadStationData() {
  try {
    const { stations, timezone } = await _dataSource.loadStations(state.city_id, state.date);
    applyStationsToState(stations, timezone);
    console.log("Station data loaded:", state.stationData);
  } catch (err) {
    console.error("Error loading station data:", err);
  }
}

/**
 * Save normalized stations into state, attaching timing fields.
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
 * Check whether trip data exists for a date, via the selected source.
 * @param {string} date - Date to check.
 * @returns {Promise<boolean>} True when trip data exists.
 */
export async function checkTripsDataExists(date) {
  try {
    return await _dataSource.checkTripExists(state.city_id, date);
  } catch (err) {
    console.error("Error checking trip data file:", err);
    return false;
  }
}