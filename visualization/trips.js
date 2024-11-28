const map = L.map('map').setView([50.5839167, 8.6792777], 12);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

let tripsData = [];
let activeRoutes = {};
let timer = null;
let isPlaying = false;

fetch('data/trips_2024-11-19.json')
    .then(response => response.json())
    .then(data => {
        tripsData = data;
        console.log('Trips data loaded:', tripsData);

        populateRouteTable();
    })
    .catch(err => console.error('Error loading trip data:', err));

function formatTime(minutes) {
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

function updateMap(currentTimeMinutes) {
    if (!tripsData || tripsData.length === 0) {
        console.error('Trips data is not loaded yet.');
        return;
    }

    const currentTime = new Date(tripsData[0].start_time);
    currentTime.setHours(0, 0, 0, 0);
    currentTime.setMinutes(currentTimeMinutes);

    console.log('Slider time:', formatTime(currentTimeMinutes));
    console.log('Current time:', currentTime);

    tripsData.forEach((trip, index) => {
        const tripStart = new Date(trip.start_time);
        const tripEnd = new Date(trip.end_time);

        if (currentTime >= tripStart && currentTime <= tripEnd) {
            console.log(`Trip ${index} is active at this time.`);

            const pathCoordinates = [];

            trip.segments.forEach(segment => {
                const [lat, lon, timestamp] = segment;
                const segmentTime = new Date(timestamp);

                if (segmentTime <= currentTime) {
                    pathCoordinates.push([lat, lon]);
                }
            });

            if (pathCoordinates.length > 0) {
                if (activeRoutes[index]) {
                    map.removeLayer(activeRoutes[index]);
                }

                activeRoutes[index] = L.polyline(pathCoordinates, { color: 'blue', weight: 3 }).addTo(map);
            }
        } else {
            console.log(`Trip ${index} is inactive at this time.`);

            if (activeRoutes[index]) {
                map.removeLayer(activeRoutes[index]);
                delete activeRoutes[index];
            }
        }
    });
}
const tripDateElement = document.getElementById('trip-date');
const currentTimeElement = document.getElementById('current-time');
const tripCountElement = document.getElementById('trip-count');
const bikeCountElement = document.getElementById('bike-count');


function populateRouteTable() {
    const tableBody = document.querySelector('#route-table tbody');
    tableBody.innerHTML = ''; // Clear existing rows

    tripsData.forEach((trip, index) => {
        const row = document.createElement('tr');

        // Create and append cells
        const bikeCell = document.createElement('td');
        bikeCell.textContent = trip.bike_number;
        row.appendChild(bikeCell);

        const startTimeCell = document.createElement('td');
        startTimeCell.textContent = new Date(trip.start_time).toLocaleTimeString();
        row.appendChild(startTimeCell);

        const endTimeCell = document.createElement('td');
        endTimeCell.textContent = new Date(trip.end_time).toLocaleTimeString();
        row.appendChild(endTimeCell);

        const distanceCell = document.createElement('td');
        distanceCell.textContent = trip.distance.toFixed(2);
        row.appendChild(distanceCell);

        tableBody.appendChild(row);
    });
}

function updateInfoBox(currentTimeMinutes) {
    if (!tripsData || tripsData.length === 0) return;

    const tripDate = new Date(tripsData[0].start_time).toLocaleDateString();
    tripDateElement.textContent = tripDate;

    currentTimeElement.textContent = formatTime(currentTimeMinutes);

    let activeTrips = 0;
    const activeBikes = new Set();

    tripsData.forEach(trip => {
        const tripStart = new Date(trip.start_time);
        const tripEnd = new Date(trip.end_time);

        if (currentTimeMinutes >= minutesSinceMidnight(tripStart) &&
            currentTimeMinutes <= minutesSinceMidnight(tripEnd)) {
            activeTrips++;
            activeBikes.add(trip.bike_number);
        }
    });

    tripCountElement.textContent = tripsData.length; // Total trips that day
    bikeCountElement.textContent = activeBikes.size; // Unique active bikes
}

function minutesSinceMidnight(date) {
    return date.getHours() * 60 + date.getMinutes();
}


const slider = document.getElementById('time-slider');
const timeDisplay = document.getElementById('time-display');
const playButton = document.getElementById('play-button');

slider.addEventListener('input', (event) => {
    const currentTimeMinutes = parseInt(event.target.value, 10);
    timeDisplay.textContent = `Time: ${formatTime(currentTimeMinutes)}`;
    updateMap(currentTimeMinutes);
    updateInfoBox(currentTimeMinutes);
});

playButton.addEventListener('click', () => {
    if (isPlaying) {
        clearInterval(timer);
        isPlaying = false;
        playButton.textContent = 'Play';
    } else {
        const maxTime = parseInt(slider.max, 10);
        let currentTimeMinutes = parseInt(slider.value, 10);

        timer = setInterval(() => {
            if (currentTimeMinutes >= maxTime) {
                clearInterval(timer);
                isPlaying = false;
                playButton.textContent = 'Play';
                return;
            }

            currentTimeMinutes += 1;
            slider.value = currentTimeMinutes;
            timeDisplay.textContent = `Time: ${formatTime(currentTimeMinutes)}`;
            updateMap(currentTimeMinutes);
            updateInfoBox(currentTimeMinutes);
        }, 100);

        isPlaying = true;
        playButton.textContent = 'Pause';
    }
});

