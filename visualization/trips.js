const map = L.map('map').setView([50.5839167, 8.6792777], 12);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

const state = {
    tripsData: [],
    activeRoutes: {},
    isPlaying: false,
    timer: null,
    currentTimeMinutes: 0,
};

const formatTime = (minutes) => {
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
};

const minutesSinceMidnight = (date) => date.getHours() * 60 + date.getMinutes();

async function loadTripsData() {
    try {
        const response = await fetch('data/trips_2024-11-19.json');
        state.tripsData = await response.json();
        console.log('Trips data loaded:', state.tripsData);

        populateRouteTable();
        updateAllComponents();
    } catch (err) {
        console.error('Error loading trip data:', err);
    }
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
}

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

loadTripsData();
