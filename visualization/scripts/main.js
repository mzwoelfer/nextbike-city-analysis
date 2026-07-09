import state from './state.js';
import { initializeMap } from './map.js';
import { loadStationData, loadTripsData, checkTripsDataExists, loadFirstAvailableData, loadAvailableFiles } from './data.js';
import { togglePlay, updateSlider } from './playback.js';
import { populateRouteTable, highlightTableRow } from './table.js';
import { plotStationsOnMap, updateStationMarkers } from './stations.js';
import { initializeBackToTop } from './navigation.js';
import { drawTrips, highlightTripOnMap } from './trips.js';
import { buildTripsPerMinute, initChart, updateChartDot, drawDurationHistogram, drawDistanceHistogram, drawHourHistogram } from './chart.js';
import { initCalendar, refreshCalendar } from './calendar.js';

let updateThrottle;

const previousDayButton = document.getElementById('previous-day');
const nextDayButton = document.getElementById('next-day');
const citySelector = document.getElementById('city-selector');
const timeSlider = document.getElementById('time-slider');
const playButton = document.getElementById('play-button');

/**
 * Render the selected trip date label.
 * @param {string} selectedDate - Selected date string.
 */
function renderTripDateLabel(selectedDate) {
    const tripDateElement = document.getElementById('trip-date');
    if (tripDateElement) {
        tripDateElement.textContent = selectedDate;
    }
}

/**
 * Count how many trips are active at a given minute.
 * @param {Array<Object>} trips - Loaded trip rows.
 * @param {number} currentMinute - Current minute in the selected city.
 * @returns {number} Number of active trips.
 */
function countActiveTripsAtMinute(trips, currentMinute) {
    return trips.reduce((activeTripCount, trip) => {
        if (trip.start_minute_city == null || trip.end_minute_city == null) {
            return activeTripCount;
        }

        if (currentMinute >= trip.start_minute_city && currentMinute <= trip.end_minute_city) {
            return activeTripCount + 1;
        }

        return activeTripCount;
    }, 0);
}

/**
 * Count available bikes at a given minute.
 * @param {Array<Object>} stations - Loaded station timeline rows.
 * @param {number} currentMinute - Current minute in the selected city.
 * @returns {number} Available bike count.
 */
function countAvailableBikesAtMinute(stations, currentMinute) {
    const latestBikeCountsByStation = {};

    stations.forEach(({ id, minute_city, bike_count }) => {
        if (minute_city == null || minute_city > currentMinute) {
            return;
        }

        latestBikeCountsByStation[id] = bike_count;
    });

    return Object.values(latestBikeCountsByStation).reduce((sum, count) => sum + count, 0);
}

/**
 * Render dashboard statistics for the current playback minute.
 * @returns {void}
 */
function renderDashboardStats() {
    const { tripsData, stationData, currentTimeMinutes, date } = state;

    if (!tripsData || tripsData.length === 0) {
        return;
    }

    const activeTripCount = countActiveTripsAtMinute(tripsData, currentTimeMinutes);
    const availableBikeCount = countAvailableBikesAtMinute(stationData, currentTimeMinutes);

    renderTripDateLabel(date);

    document.getElementById('trip-count').textContent = tripsData.length;
    document.getElementById('active-trips-count').textContent = activeTripCount;
    document.getElementById('bike-count').textContent = availableBikeCount;

    document.getElementById('sb-trip-count').textContent = tripsData.length;
    document.getElementById('sb-active-trips').textContent = activeTripCount;
    document.getElementById('sb-bike-count').textContent = availableBikeCount;

    updateChartDot(currentTimeMinutes);
}

/**
 * Render timeline and histogram charts.
 * @returns {void}
 */
function renderCharts() {
    requestAnimationFrame(() => {
        const tripChartCanvas = document.getElementById('trips-chart');
        const tripCountsPerMinute = buildTripsPerMinute(state.tripsData, state.city_timezone);

        initChart(tripChartCanvas, tripCountsPerMinute, (selectedMinute) => {
            state.currentTimeMinutes = selectedMinute;
            updateAllComponents();
        });

        drawDurationHistogram(
            document.getElementById('duration-chart'),
            state.tripsData
        );
        drawDistanceHistogram(
            document.getElementById('distance-chart'),
            state.tripsData
        );
        drawHourHistogram(
            document.getElementById('hour-chart'),
            state.tripsData,
            state.city_timezone
        );
        refreshCalendar();
    });
}

/**
 * Render the empty-data startup state.
 * @returns {void}
 */
function renderNoDataState() {
    renderTripDateLabel('No processed data yet');
}

/**
 * Redraw all time-dependent visualization components.
 * @returns {void}
 */
export function updateAllComponents() {
    updateSlider();
    if (updateThrottle) {
        cancelAnimationFrame(updateThrottle);
    }

    updateThrottle = requestAnimationFrame(() => {
        drawTrips();
        updateStationMarkers();
        renderDashboardStats();
    });
}

/**
 * Highlight a trip in both the map and route table.
 * @param {number} index - Trip index in state.tripsData.
 */
export function highlightTrip(index) {
    highlightTripOnMap(index);
    highlightTableRow(index);
    updateSlider();
}

/**
 * Render city options into the dropdown.
 * @returns {void}
 */
function renderCityOptions() {
    citySelector.innerHTML = "";

    console.log('CITIES IN DROPDOWN', Object.keys(state.cities));
    Object.entries(state.cities).forEach(([cityName, cityId]) => {
        const option = document.createElement('option');
        option.value = cityId;
        option.textContent = cityName;
        if (parseInt(cityId, 10) === state.city_id) {
            option.selected = true;
        }
        citySelector.appendChild(option);
    });
}

/**
 * Load all visualization data for the selected city.
 * @param {string|number} cityId - Selected city id.
 * @returns {Promise<void>}
 */
async function loadCityVisualization(cityId) {
    state.city_id = cityId;
    await loadTripsData();
    initializeMap(state.city_lat, state.city_lng);
    populateRouteTable();

    await loadStationData();
    plotStationsOnMap();
    await updateDateNavigationAvailability();
    updateAllComponents();
    renderCharts();
}

/**
 * Handle city dropdown changes.
 * @param {Event} event - Change event from the city dropdown.
 * @returns {Promise<void>}
 */
async function handleCitySelectionChange(event) {
    const cityId = parseInt(event.target.value, 10);
    await loadCityVisualization(cityId);
}

/**
 * Update previous and next day button states.
 * @returns {Promise<void>}
 */
async function updateDateNavigationAvailability() {
    const prevDate = new Date(state.date);
    prevDate.setDate(prevDate.getDate() - 1);
    const nextDate = new Date(state.date);
    nextDate.setDate(nextDate.getDate() + 1);

    const prevExists = await checkTripsDataExists(prevDate.toISOString().split('T')[0]);
    const nextExists = await checkTripsDataExists(nextDate.toISOString().split('T')[0]);

    previousDayButton.disabled = !prevExists;
    nextDayButton.disabled = !nextExists;
}

/**
 * Move the current date by one day and reload the visualization.
 * @param {number} dayOffset - Day delta to apply.
 * @returns {Promise<void>}
 */
async function shiftDisplayedDate(dayOffset) {
    if (dayOffset < 0) {
        state.previousDay();
    } else {
        state.nextDay();
    }

    await loadCityVisualization(state.city_id);
}

/**
 * Handle timeline slider input.
 * @param {Event} event - Input event from the slider.
 */
function handleTimeSliderInput(event) {
    state.currentTimeMinutes = parseInt(event.target.value, 10);
    updateAllComponents();
}

/**
 * Bind city dropdown listeners.
 * @returns {void}
 */
function bindCitySelectionDropdown() {
    citySelector.addEventListener('change', handleCitySelectionChange);
}

/**
 * Bind previous and next day controls.
 * @returns {void}
 */
function bindDayNavigationControls() {
    previousDayButton.addEventListener('click', async () => {
        await shiftDisplayedDate(-1);
    });

    nextDayButton.addEventListener('click', async () => {
        await shiftDisplayedDate(1);
    });
}

/**
 * Bind playback controls.
 * @returns {void}
 */
function bindPlaybackControls() {
    timeSlider.addEventListener('input', handleTimeSliderInput);
    playButton.addEventListener('click', () => togglePlay());
}

/**
 * Bind calendar callbacks.
 * @returns {void}
 */
function bindCalendar() {
    initCalendar((dateStr) => {
        state.date = dateStr;
        loadCityVisualization(state.city_id);
    });
}

/**
 * Start the visualization application.
 * @returns {Promise<void>}
 */
async function initializeVisualizationApp() {
    bindCitySelectionDropdown();
    bindDayNavigationControls();
    bindPlaybackControls();
    initializeBackToTop();
    bindCalendar();

    state.availableFiles = await loadAvailableFiles();
    const hasInitialData = await loadFirstAvailableData();
    renderCityOptions();

    if (hasInitialData) {
        await loadCityVisualization(state.city_id);
        return;
    }

    renderNoDataState();
}

initializeVisualizationApp();
