import state from './state.js';
import { getMap } from "./map.js";
import { minutesSinceMidnight } from './utils.js';

export const plotStationsOnMap = () => {
    const map = getMap();
    const { stationData } = state;

    stationData.forEach((station) => {
        const { latitude, longitude, id } = station;

        const marker = L.circleMarker([latitude, longitude], {
            radius: 6,
            color: 'var(--bg-dark-2)',
            fillColor: 'var(--bg-dark-2)',
            fillOpacity: 1,
        }).addTo(map);

        const bikeCountLabel = L.divIcon({
            className: 'bike-count-label',
            html: `<div class="bike-count-text"></div>`,
        });

        const labelMarker = L.marker([latitude, longitude], { icon: bikeCountLabel, interactive: false }).addTo(map);

        state.markerMap[id] = { marker, labelMarker };
    });
}


export const updateStationMarkers = () => {
    const { stationData, currentTimeMinutes, markerMap, city_timezone } = state;

    if (!stationData || stationData.length === 0 || !markerMap) return;

    stationData.forEach(({ id, minute, bike_count }) => {
        const stationTime = minutesSinceMidnight(new Date(minute), city_timezone);
        if (stationTime <= currentTimeMinutes) {
            const stationMarkers = markerMap[id];
            if (stationMarkers && stationMarkers.labelMarker) {
                const labelElement = stationMarkers.labelMarker.getElement().querySelector('.bike-count-text');
                if (labelElement) {
                    labelElement.textContent = bike_count;
                }
            }
        }
    });
}
