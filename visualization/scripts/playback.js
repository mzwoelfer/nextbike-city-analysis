import state from './state.js';
import { formatTime } from './utils.js';

export function updatePlayButtonUI(){
    const playButton = document.getElementById('play-button'); 
    playButton.textContent = state.isPlaying ? 'Pause' : 'Play';
}


export function updateSlider(){
    document.getElementById('time-slider').value = state.currentTimeMinutes;
    document.getElementById('time-display').textContent = `${formatTime(state.currentTimeMinutes)}`;
}
