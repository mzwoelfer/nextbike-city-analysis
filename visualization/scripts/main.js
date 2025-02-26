import state from './state.js';
import { initializeMap } from './map.js';
import { loadStationData, loadTripsData, checkTripsDataExists, loadFirstAvailableData, loadAvailableFiles } from './data.js';
import { togglePlay, updateSlider } from './playback.js';
import { formatTime, minutesSinceMidnight } from './utils.js';
import { populateRouteTable, highlightTableRow } from './table.js';
import { plotStationsOnMap, updateStationMarkers } from './stations.js';
import { initializeBackToTop } from './navigation.js';
import { drawTrips, highlightTripOnMap } from './trips.js';

let updateThrottle;

function updateInfoBox() {
    const { tripsData, currentTimeMinutes } = state;

    if (!tripsData || tripsData.length === 0) return;

    const tripDate = new Date(tripsData[0].start_time).toLocaleDateString();
    document.getElementById('trip-date').textContent = tripDate;

    let activeTrips = 0;
    const activeBikes = new Set();

    tripsData.forEach((trip) => {
        const tripStart = new Date(trip.start_time);
        const tripEnd = new Date(trip.end_time);

        if (currentTimeMinutes >= minutesSinceMidnight(tripStart) &&
            currentTimeMinutes <= minutesSinceMidnight(tripEnd)) {
            activeTrips++;
            activeBikes.add(trip.bike_number);
        }
    });

    document.getElementById('trip-count').textContent = tripsData.length; // Total trips that day
    document.getElementById('bike-count').textContent = activeBikes.size; // Unique active bikes
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
async function handleCityChange(event) {
    const cityId = parseInt(event.target.value, 10);
    const cityName = Object.keys(state.cities).find(key => state.cities[key] === cityId);

    loadCityData(cityId);
}

// ++++++++++++++++++ //
// Previous/Next Day Buttons
const previousDayButton = document.getElementById('previous-day')
const nextDayButton = document.getElementById('next-day')
const citySelector = document.getElementById('city-selector')

citySelector.addEventListener('change', handleCityChange);


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
    initializeMap(state.city_lat, state.city_lng)
    populateRouteTable();

    await loadStationData();
    if (map) {
        plotStationsOnMap();
    } else {
        console.error('Map is not initialized. Cannot plot stations.');
    }
    updateButtonStates();
    updateAllComponents();

}

state.availableFiles = await loadAvailableFiles();
await loadFirstAvailableData();
populateCityDropdown();
loadCityData(state.city_id);
initializeBackToTop();
