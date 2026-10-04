import state from './state.js';
import { formatTime } from './utils.js';
import { updateAllComponents } from './main.js';

export function updatePlayButtonUI() {
    const playButton = document.getElementById('play-button');
    playButton.textContent = state.isPlaying ? '⏸' : '▶';
}

export function updateSlider() {
    document.getElementById('time-slider').value = state.currentTimeMinutes;
    document.getElementById('time-display').textContent = `${formatTime(state.currentTimeMinutes)}`;
}


export function togglePlay() {
    if (state.isPlaying) {
        stopPlayback();
    } else {
        startPlayback();
    }
}

export function stopPlayback() {
    clearInterval(state.timer);
    state.isPlaying = false;
    updatePlayButtonUI();
}

function firstAvailableMinute() {
    const minutes = [
        ...state.stationData.map((station) => station.minute_city),
        ...state.bikeData.map((bike) => bike.minute_city),
        ...state.tripsData.map((trip) => trip.start_minute_city),
    ].filter(Number.isFinite);

    return minutes.length ? Math.min(...minutes) : null;
}

export function startPlayback() {
    const playback_interval_milliseconds = 100;
    const maxTime = parseInt(document.getElementById('time-slider').max, 10);
    const firstMinute = firstAvailableMinute();

    if (firstMinute !== null && state.currentTimeMinutes < firstMinute) {
        state.currentTimeMinutes = firstMinute;
        updateAllComponents();
    }

    state.timer = setInterval(() => {
        if (state.currentTimeMinutes >= maxTime) {
            stopPlayback();
            return;
        }

        state.currentTimeMinutes++;
        updateSlider();
        updateAllComponents();
    }, playback_interval_milliseconds);

    state.isPlaying = true;
    updatePlayButtonUI();
}
