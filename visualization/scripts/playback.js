import state from './state.js';
import { formatTime } from './utils.js';
import { updateAllComponents } from './trips.js';

export function updatePlayButtonUI() {
    const playButton = document.getElementById('play-button');
    playButton.textContent = state.isPlaying ? 'Pause' : 'Play';
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

export function startPlayback() {
    const playback_interval_milliseconds = 100;
    const maxTime = parseInt(document.getElementById('time-slider').max, 10);

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
