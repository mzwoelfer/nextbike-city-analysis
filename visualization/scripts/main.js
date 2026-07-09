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

function updateInfoBox() {
    const { tripsData, currentTimeMinutes } = state;

    if (!tripsData || tripsData.length === 0) return;

    const tripDate = state.date;
    document.getElementById('trip-date').textContent = tripDate;

    let activeTrips = 0;

    tripsData.forEach((trip) => {
        const tripStartMinutes = trip.start_minute_city;
        const tripEndMinutes = trip.end_minute_city;
        if (tripStartMinutes == null || tripEndMinutes == null) {
            return;
        }

        if (currentTimeMinutes >= tripStartMinutes &&
            currentTimeMinutes <= tripEndMinutes) {
            activeTrips++;
        }
    });
    const latestCount = {};
        state.stationData.forEach(({ id, minute_city, bike_count }) => {
            if (minute_city == null) {
                return;
            }
            if (minute_city <= currentTimeMinutes) {
                latestCount[id] = bike_count;
            }
        });
    const availableBikes = Object.values(latestCount).reduce((s, n) => s + n, 0);


    // Play area stats
    document.getElementById('trip-count').textContent = tripsData.length;
    document.getElementById('active-trips-count').textContent = activeTrips;
    document.getElementById('bike-count').textContent = availableBikes;

    // Sidebar stats
    document.getElementById('sb-trip-count').textContent = tripsData.length;
    document.getElementById('sb-active-trips').textContent = activeTrips;
    document.getElementById('sb-bike-count').textContent = availableBikes;

    // Chart dot
    updateChartDot(currentTimeMinutes);
}

export function updateAllComponents() {
    updateSlider()
    if (updateThrottle) {
        cancelAnimationFrame(updateThrottle);
    }

    updateThrottle = requestAnimationFrame(() => {
        drawTrips();
        updateStationMarkers();
        updateInfoBox();
    });
}

// ++++++++++++++ //
// HIGHLIGHT TRIP //
export function highlightTrip(index) {
    highlightTripOnMap(index);
    highlightTableRow(index);
    updateSlider();
}

// +++++++++++++++++++++++ //
// City selection dropdown
function populateCityDropdown() {
    const citySelector = document.getElementById('city-selector');
    citySelector.innerHTML = "";

    console.log("CITIES IN DROPDOWN", Object.keys(state.cities))
    Object.entries(state.cities).forEach(([cityName, cityId]) => {
        const option = document.createElement("option");
        option.value = cityId;
        option.textContent = cityName;
        if (parseInt(cityId, 10) === state.city_id) {
            option.selected = true;
        }
        citySelector.appendChild(option);
    })
}

// ++++++++++++++++++++++++++ //
// City selection
async function changeCityData(event) {
    const cityId = parseInt(event.target.value, 10);
    const cityName = Object.keys(state.cities).find(key => state.cities[key] === cityId);

    loadCityData(cityId);
}

// ++++++++++++++++++ //
// Previous/Next Day Buttons
const previousDayButton = document.getElementById('previous-day')
const nextDayButton = document.getElementById('next-day')
const citySelector = document.getElementById('city-selector')

citySelector.addEventListener('change', changeCityData);


const updateButtonStates = async () => {
    const prevDate = new Date(state.date);
    prevDate.setDate(prevDate.getDate() - 1);
    const nextDate = new Date(state.date);
    nextDate.setDate(nextDate.getDate() + 1);

    const prevExists = await checkTripsDataExists(prevDate.toISOString().split('T')[0]);
    const nextExists = await checkTripsDataExists(nextDate.toISOString().split('T')[0]);

    previousDayButton.disabled = !prevExists;
    nextDayButton.disabled = !nextExists;
};

previousDayButton.addEventListener('click', async () => {
    state.previousDay()
    await loadCityData(state.city_id)
})

nextDayButton.addEventListener('click', async () => {
    state.nextDay()
    await loadCityData(state.city_id)
})


// ++++++++++ //
// Timeslider
document.getElementById('time-slider').addEventListener('input', (event) => {
    state.currentTimeMinutes = parseInt(event.target.value, 10);
    updateAllComponents();
});

document.getElementById('play-button').addEventListener('click', () => togglePlay());

async function loadCityData(city_id) {
    state.city_id = city_id;
    await loadTripsData();
    initializeMap(state.city_lat, state.city_lng);
    populateRouteTable();

    await loadStationData();
    plotStationsOnMap();
    updateButtonStates();
    updateAllComponents();

    // Init the sidebar chart after layout has settled
    requestAnimationFrame(() => {
        const canvas = document.getElementById('trips-chart');
        const counts = buildTripsPerMinute(state.tripsData, state.city_timezone);
        initChart(canvas, counts, (minute) => {
            state.currentTimeMinutes = minute;
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

state.availableFiles = await loadAvailableFiles();
const hasInitialData = await loadFirstAvailableData();
populateCityDropdown();

if (hasInitialData) {
    loadCityData(state.city_id);
} else {
    const dateElement = document.getElementById('trip-date');
    if (dateElement) {
        dateElement.textContent = 'No processed data yet';
    }
}

initializeBackToTop();
initCalendar((dateStr) => {
    state.date = dateStr;
    loadCityData(state.city_id);
});
