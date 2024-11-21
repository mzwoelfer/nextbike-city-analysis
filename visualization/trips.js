const map = L.map('map').setView([50.585716, 8.657575], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

let routeLayer = null;
let tripData = null;

fetch('data/timestamped_06-11-2024-trips.json')
    .then(response => response.json())
    .then(data => {
        tripData = data[0]; 
        console.log('Trip data loaded:', tripData);
    })
    .catch(err => console.error('Error loading trip data:', err));

function formatTime(minutes) {
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}


function updateMap(currentTimeMinutes) {
    if (!tripData) {
        console.error('Trip data is not loaded yet.');
        return;
    }

    const tripStart = new Date(tripData.start_time);
    const tripEnd = new Date(tripData.end_time);

    const currentTime = new Date(tripStart);
    currentTime.setHours(0, 0, 0, 0); 
    currentTime.setMinutes(currentTimeMinutes);

    console.log('Slider time:', formatTime(currentTimeMinutes));
    console.log('Trip start:', tripStart, 'Trip end:', tripEnd, 'Current time:', currentTime);

    if (routeLayer) {
        map.removeLayer(routeLayer);
    }

    if (currentTime >= tripStart && currentTime <= tripEnd) {
        console.log('Trip is active at this time.');
        const pathCoordinates = [];

        tripData.segments.forEach(segment => {
            const [lat, lon, timestamp] = segment;
            const segmentTime = new Date(timestamp);
            console.log('Segment:', segment, 'Segment time:', segmentTime);

            if (segmentTime <= currentTime) {
                console.log('Adding segment:', [lat, lon]);
                pathCoordinates.push([lat, lon]);
            }
        });

        if (pathCoordinates.length > 0) {
            console.log('Drawing polyline with coordinates:', pathCoordinates);
            routeLayer = L.polyline(pathCoordinates, { color: 'blue', weight: 3 }).addTo(map);
        } else {
            console.log('No coordinates to draw.');
        }
    } else {
        console.log('Trip is inactive at this time.');
    }
}


const slider = document.getElementById('time-slider');
const timeDisplay = document.getElementById('time-display');

slider.addEventListener('input', (event) => {
    const currentTimeMinutes = parseInt(event.target.value, 10);
    timeDisplay.textContent = `Time: ${formatTime(currentTimeMinutes)}`;
    updateMap(currentTimeMinutes);
});

