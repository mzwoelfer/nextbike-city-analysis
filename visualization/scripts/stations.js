import state from './state.js';
import { getMap } from "./map.js";

export const plotStationsOnMap = () => {
    const map = getMap();
    const { stationData } = state;

    stationData.forEach((station) => {
        const { latitude, longitude, id } = station;

        const marker = L.circleMarker([latitude, longitude], {
            radius: 6,
            color: '#7C0A02',
            fillColor: '#7C0A02',
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

