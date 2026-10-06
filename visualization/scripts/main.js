import state from './state.js';
import { getMap, initializeMap } from './map.js';
import { loadBikeData, loadStationData, loadTripsData, checkTripsDataExists, loadFirstAvailableData, loadAvailableFiles, getAvailableMonths, loadTripsForMonth } from './data.js';
import { buildMonthlyTripsCsv } from './csvExport.js';
import { togglePlay, updateSlider } from './playback.js';
import { populateRouteTable, populateUniqueRoutesTable, highlightTableRow } from './table.js';
import { plotStationsOnMap, updateBikeMarkers, updateStationMarkers } from './stations.js';
import { initializeBackToTop } from './navigation.js';
import { drawTripsOnMap, highlightTripOnMap } from './trips.js';
import { buildTripsPerMinute, initChart, updateChartDot, drawDurationHistogram, drawDistanceHistogram, drawHourHistogram } from './chart.js';
import { initCalendar, refreshCalendar } from './calendar.js';

let updateThrottle;

const previousDayButton = document.getElementById('previous-day');
const nextDayButton = document.getElementById('next-day');
const citySelector = document.getElementById('city-selector');
const timeSlider = document.getElementById('time-slider');
const playButton = document.getElementById('play-button');
const exportMonthSelector = document.getElementById('trip-export-month');
const exportButton = document.getElementById('download-trip-csv');
const exportStatus = document.getElementById('trip-export-status');

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
    const emptyDataState = document.getElementById('empty-data-state');
    emptyDataState.hidden = false;
    document.getElementById('main-layout').hidden = true;
    document.getElementById('data-section').hidden = true;
    document.getElementById('table-view-controls').hidden = true;
    document.getElementById('route-table-container').hidden = true;
    document.getElementById('unique-routes-container').hidden = true;
    exportMonthSelector.disabled = true;
    exportButton.disabled = true;
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
        drawTripsOnMap();
        updateStationMarkers();
        updateBikeMarkers();
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
    const cities = Object.entries(state.cities);
    if (cities.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No cities available';
        citySelector.appendChild(option);
        citySelector.disabled = true;
        return;
    }

    citySelector.disabled = false;
    cities.forEach(([cityName, cityId]) => {
        const option = document.createElement('option');
        option.value = cityId;
        option.textContent = cityName;
        if (parseInt(cityId, 10) === state.city_id) {
            option.selected = true;
        }
        citySelector.appendChild(option);
    });
}

function renderExportMonths(cityId) {
    const months = getAvailableMonths(cityId);
    exportMonthSelector.replaceChildren();

    months.forEach((month) => {
        const option = document.createElement('option');
        option.value = month;
        option.textContent = new Intl.DateTimeFormat(undefined, {
            month: 'long',
            year: 'numeric',
            timeZone: 'UTC',
        }).format(new Date(`${month}-01T00:00:00Z`));
        exportMonthSelector.appendChild(option);
    });

    exportButton.disabled = months.length === 0;
    exportStatus.textContent = '';
}

async function downloadMonthlyTrips() {
    const month = exportMonthSelector.value;
    if (!month) return;

    exportButton.disabled = true;
    exportStatus.textContent = 'Preparing CSV...';

    try {
        const { trips } = await loadTripsForMonth(state.city_id, month);
        if (trips.length === 0) {
            exportStatus.textContent = 'No trips available for this month.';
            return;
        }

        const cityName = citySelector.selectedOptions[0]?.textContent || state.city_id;
        const csv = buildMonthlyTripsCsv(trips, state.city_id, cityName);
        const blob = new Blob(['\uFEFF', csv], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `nextbike_trips_${state.city_id}_${month}.csv`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 0);
        exportStatus.textContent = `${trips.length} trips exported.`;
    } catch (error) {
        console.error('Error exporting monthly trips:', error);
        exportStatus.textContent = 'CSV export failed. Check the available trip data and retry.';
    } finally {
        exportButton.disabled = getAvailableMonths(state.city_id).length === 0;
    }
}

/**
 * Load all visualization data for the selected city.
 * @param {string|number} cityId - Selected city id.
 * @returns {Promise<void>}
 */
async function loadCityVisualization(cityId) {
    state.city_id = cityId;
    state.currentTimeMinutes = 0;
    state.stationData = [];
    state.bikeData = [];
    renderExportMonths(cityId);
    await loadTripsData();
    const hasRoutedTrips = state.tripsData.some(
        (trip) => Array.isArray(trip.coordinates) && trip.coordinates.length > 0,
    );
    initializeMap(state.city_lat, state.city_lng);
    populateRouteTable(highlightTrip);
    populateUniqueRoutesTable();

    await loadStationData();
    await loadBikeData();
    if (!hasRoutedTrips) {
        const station = state.stationData.find(
            ({ latitude, longitude }) => Number.isFinite(Number(latitude)) && Number.isFinite(Number(longitude)),
        );
        if (station) {
            state.city_lat = Number(station.latitude);
            state.city_lng = Number(station.longitude);
            getMap().setView([state.city_lat, state.city_lng]);
        }
    }

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
    playButton.addEventListener('click', () => togglePlay(updateAllComponents));
}

function bindTableViews() {
    const buttons = document.querySelectorAll('#table-view-controls button');
    const panels = document.querySelectorAll('[data-table-panel]');

    buttons.forEach((button) => {
        button.addEventListener('click', () => {
            const view = button.dataset.tableView;
            buttons.forEach((otherButton) => {
                otherButton.setAttribute('aria-pressed', String(otherButton === button));
            });
            panels.forEach((panel) => {
                panel.hidden = panel.dataset.tablePanel !== view;
            });
        });
    });
}

function bindExportControls() {
    exportButton.addEventListener('click', downloadMonthlyTrips);
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
    bindTableViews();
    bindExportControls();
    initializeBackToTop();
    bindCalendar();

    state.availableFiles = await loadAvailableFiles();
    const hasInitialData = await loadFirstAvailableData();
    renderCityOptions();
    renderExportMonths(state.city_id);

    if (hasInitialData) {
        await loadCityVisualization(state.city_id);
        return;
    }

    renderNoDataState();
}

initializeVisualizationApp();
