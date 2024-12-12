const state = {
    city_id: 467,
    city_lat: 0,
    city_lng: 0,
    tripsData: [],
    activeRoutes: {},
    stationData: [],
    isPlaying: false,
    timer: null,
    currentTimeMinutes: 0,
};

let map;
const initializeMap = (lat, lng) => {
    if (map) {
        map.remove();
    }

    map = L.map('map').setView([lat, lng], 12);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);
}

const formatTime = (minutes) => {
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
};

const minutesSinceMidnight = (date) => date.getHours() * 60 + date.getMinutes();

async function loadTripsData() {
    try {
        const response = await fetch('data/467_trips_2024-12-06.json');
        const data = await response.json();

        state.tripsData = data["trips"];
        state.city_lat = data["city_info"]["lat"];
        state.city_lng = data["city_info"]["lng"];

        console.log('Trips data loaded:', state.tripsData);

        initializeMap(state.city_lat, state.city_lng)

        populateRouteTable();
        updateAllComponents();

        await loadStationData();
    } catch (err) {
        console.error('Error loading trip data:', err);
    }
}

async function loadStationData() {
    try {
        const response = await fetch('data/467_stations_2024-12-06.json');
        state.stationData = await response.json();
        console.log('Station data loaded:', state.stationData);

        if (map) {
            plotStationsOnMap();
        } else {
            console.error('Map is not initialized. Cannot plot stations.');
        }
    } catch (err) {
        console.error('Error loading station data:', err);
    }
}

function plotStationsOnMap() {
    const { stationData } = state;
    stationData.forEach((station) => {
        const { latitude, longitude, name } = station;
        L.circleMarker([latitude, longitude], {
            radius: 2,
            color: 'orange',
            fillColor: 'orange',
            fillOpacity: 0.3,
        })
            .bindPopup(`<strong>${name}</strong>`)
            .addTo(map);
    });
}

function updateMap() {
    const { tripsData, currentTimeMinutes, activeRoutes } = state;

    if (!tripsData || tripsData.length === 0) return;

    const currentTime = new Date(tripsData[0].start_time);
    currentTime.setHours(0, 0, 0, 0);
    currentTime.setMinutes(currentTimeMinutes);

    tripsData.forEach((trip, index) => {
        const tripStart = new Date(trip.start_time);
        const tripEnd = new Date(trip.end_time);

        if (currentTime >= tripStart && currentTime <= tripEnd) {
            const pathCoordinates = trip.segments
                .filter(([_, __, timestamp]) => new Date(timestamp) <= currentTime)
                .map(([lat, lon]) => [lat, lon]);

            if (pathCoordinates.length > 0) {
                if (activeRoutes[index]) {
                    map.removeLayer(activeRoutes[index]);
                }
                activeRoutes[index] = L.polyline(pathCoordinates, { color: 'blue', weight: 3 }).addTo(map);
            }
        } else {
            if (activeRoutes[index]) {
                map.removeLayer(activeRoutes[index]);
                delete activeRoutes[index];
            }
        }
    });
}

function updateInfoBox() {
    const { tripsData, currentTimeMinutes } = state;

    if (!tripsData || tripsData.length === 0) return;

    const tripDate = new Date(tripsData[0].start_time).toLocaleDateString();
    document.getElementById('trip-date').textContent = tripDate;
    document.getElementById('current-time').textContent = formatTime(currentTimeMinutes);

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

function updateAllComponents() {
    updateMap();
    updateInfoBox();
}

function populateRouteTable() {
    const tableBody = document.querySelector('#route-table tbody');
    tableBody.innerHTML = '';

    state.tripsData.forEach((trip, index) => {
        const row = document.createElement('tr');
        row.dataset.index = index;

        row.innerHTML = `
            <td>${trip.bike_number}</td>
            <td>${new Date(trip.start_time).toLocaleTimeString()}</td>
            <td>${new Date(trip.end_time).toLocaleTimeString()}</td>
            <td>${trip.distance.toFixed(2)}</td>
            <td>${Math.floor(trip.duration / 60)}</td>
        `;

        row.addEventListener('click', () => highlightTrip(index));
        tableBody.appendChild(row);
    });
}

function highlightTrip(index) {
    const trip = state.tripsData[index];
    if (!trip) return;

    Object.values(state.activeRoutes).forEach((route) => map.removeLayer(route));
    state.activeRoutes = {};

    const pathCoordinates = trip.segments.map(([lat, lon]) => [lat, lon]);
    const selectedRoute = L.polyline(pathCoordinates, { color: 'red', weight: 4 }).addTo(map);

    if (pathCoordinates.length > 0) {
        map.panTo(pathCoordinates[0]);
    }

    state.activeRoutes[index] = selectedRoute;

    document.querySelectorAll('#route-table tbody tr').forEach((row) => row.classList.remove('active'));
    document.querySelector(`[data-index='${index}']`).classList.add('active');

    const tripStartTime = new Date(trip.start_time);
    state.currentTimeMinutes = minutesSinceMidnight(tripStartTime);

    const slider = document.getElementById('time-slider');
    slider.value = state.currentTimeMinutes;
    document.getElementById('time-display').textContent = `Time: ${formatTime(state.currentTimeMinutes)}`;
}

document.getElementById('city-selector').addEventListener('change', (event) => {
    const selectedCityId = event.target.value;
    loadCityData(selectedCityId);
});

document.getElementById('time-slider').addEventListener('input', (event) => {
    state.currentTimeMinutes = parseInt(event.target.value, 10);
    document.getElementById('time-display').textContent = `Time: ${formatTime(state.currentTimeMinutes)}`;
    updateAllComponents();
});

document.getElementById('play-button').addEventListener('click', () => {
    const { isPlaying, timer } = state;

    if (isPlaying) {
        clearInterval(timer);
        state.isPlaying = false;
        document.getElementById('play-button').textContent = 'Play';
    } else {
        const maxTime = parseInt(document.getElementById('time-slider').max, 10);

        state.timer = setInterval(() => {
            if (state.currentTimeMinutes >= maxTime) {
                clearInterval(state.timer);
                state.isPlaying = false;
                document.getElementById('play-button').textContent = 'Play';
                return;
            }

            state.currentTimeMinutes++;
            document.getElementById('time-slider').value = state.currentTimeMinutes;
            document.getElementById('time-display').textContent = `Time: ${formatTime(state.currentTimeMinutes)}`;
            updateAllComponents();
        }, 100);

        state.isPlaying = true;
        document.getElementById('play-button').textContent = 'Pause';
    }
});

async function loadCityData(city_id) {
    state.city_id = city_id;
    await loadTripsData();
    await loadStationData();
}

loadCityData(state.city_id);
