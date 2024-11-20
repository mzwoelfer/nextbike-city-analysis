const map = L.map('map').setView([50.5851475, 8.6643273], 13);

// Add OpenStreetMap tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Elements for controls
const playPauseBtn = document.getElementById('playPause');
const timeSlider = document.getElementById('timeSlider');
const currentTimeDisplay = document.getElementById('currentTime');

// Global state
let trips = [];
let currentMinute = 0;
let playing = false;
let activeMarkers = [];

// Load trips data
async function loadTrips(tripFile) {
  try {
    const response = await fetch(tripFile);
    if (!response.ok) {
      throw new Error(`Error fetching Nextbike Trip data! Status: ${response.status}`);
    }

    trips = await response.json();
  } catch (error) {
    console.error('Error loading trip data:', error);
  }
}

// Helper to convert minutes to HH:MM
function formatTime(minutes) {
  const hours = Math.floor(minutes / 60).toString().padStart(2, '0');
  const mins = (minutes % 60).toString().padStart(2, '0');
  return `${hours}:${mins}`;
}

// Animate a single trip
function animateTrip(trip) {
  const { segments, start_time, end_time } = trip;
  const durationMinutes = (new Date(end_time) - new Date(start_time)) / 60000;

  // Create a marker at the start
  const marker = L.circleMarker(segments[0], { radius: 5, color: 'red' }).addTo(map);
  activeMarkers.push(marker);

  let step = 0;
  const totalSteps = segments.length;
  const stepDuration = (durationMinutes * 60 * 1000) / totalSteps;

  const interval = setInterval(() => {
    if (step >= totalSteps - 1) {
      // Remove marker when the trip ends
      map.removeLayer(marker);
      clearInterval(interval);
      activeMarkers = activeMarkers.filter((m) => m !== marker);
      return;
    }

    // Move marker to the next segment
    marker.setLatLng(segments[step]);
    step++;
  }, stepDuration);
}

// Simulate trips at the current time
function simulateTripsAt(currentMinute) {
  // Remove active markers from the previous simulation step
  activeMarkers.forEach((marker) => map.removeLayer(marker));
  activeMarkers = [];

  const currentTime = new Date(`2024-11-06T00:00:00`);
  currentTime.setMinutes(currentMinute);

  trips.forEach((trip) => {
    const start = new Date(trip.start_time);
    const end = new Date(trip.end_time);

    if (start <= currentTime && end >= currentTime) {
      animateTrip(trip);
    }
  });
}

// Handle play/pause
function togglePlayPause() {
  playing = !playing;
  playPauseBtn.textContent = playing ? 'Pause' : 'Play';

  if (playing) {
    runSimulation();
  }
}

// Simulation loop
function runSimulation() {
  if (!playing) return;

  simulateTripsAt(currentMinute);

  if (currentMinute < 1439) {
    currentMinute++;
    timeSlider.value = currentMinute;
    currentTimeDisplay.textContent = formatTime(currentMinute);
    setTimeout(runSimulation, 100); // Adjust speed as needed
  } else {
    playing = false;
    playPauseBtn.textContent = 'Play';
  }
}

// Event listeners
playPauseBtn.addEventListener('click', togglePlayPause);

timeSlider.addEventListener('input', (e) => {
  currentMinute = parseInt(e.target.value, 10);
  currentTimeDisplay.textContent = formatTime(currentMinute);
  simulateTripsAt(currentMinute);
});

// Initialize map and load data
loadTrips('trips_2024-11-06.json');