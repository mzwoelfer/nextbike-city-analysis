import state from './state.js';
import { getMap } from "./map.js";

export const plotStationsOnMap = () => {
    const map = getMap();
    const { stationData } = state;

    Object.values(state.markerMap).forEach(({ marker, labelMarker }) => {
        map.removeLayer(marker);
        map.removeLayer(labelMarker);
    });
    Object.values(state.bikeMarkerMap).forEach((marker) => map.removeLayer(marker));
    state.markerMap = {};
    state.bikeMarkerMap = {};

    const uniqueStations = new Map();
    stationData.forEach((station) => uniqueStations.set(station.id, station));

    uniqueStations.forEach((station) => {
        const { latitude, longitude, id } = station;

        const marker = L.circleMarker([latitude, longitude], {
            radius: 8,
            color: '#222222',
            fillColor: '#222222',
            fillOpacity: 1,
        }).addTo(map);
        marker.bindPopup(createStationPopupContent({
            ...station,
            bike_count: 0,
            bike_type_counts: {},
        }));

        const bikeCountLabel = L.divIcon({
            className: 'bike-count-label',
            html: `<div class="bike-count-text"></div>`,
        });

        const labelMarker = L.marker([latitude, longitude], { icon: bikeCountLabel, interactive: false }).addTo(map);

        state.markerMap[id] = { marker, labelMarker };
    });
}


export const updateStationMarkers = () => {
    const { stationData, currentTimeMinutes, markerMap } = state;

    if (!stationData || stationData.length === 0 || !markerMap) return;

    const latestStations = new Map();
    stationData.forEach((station) => {
        if (station.minute_city <= currentTimeMinutes) {
            latestStations.set(station.id, station);
        }
    });

    latestStations.forEach((station, id) => {
        const stationMarkers = markerMap[id];
        if (!stationMarkers) return;

        const labelElement = stationMarkers.labelMarker.getElement()?.querySelector('.bike-count-text');
        if (labelElement) labelElement.textContent = station.bike_count;
        stationMarkers.marker.bindPopup(createStationPopupContent(station));
    });
}

export const updateBikeMarkers = () => {
    const map = getMap();
    const latestBikes = new Map();

    state.bikeData.forEach((bike) => {
        if (bike.minute_city <= state.currentTimeMinutes) {
            latestBikes.set(String(bike.bike_number), bike);
        }
    });

    const activeBikeNumbers = new Set();
    latestBikes.forEach((bike, bikeNumber) => {
        if (bike.station_number != null && Number(bike.station_number) !== 0) return;
        if (!Number.isFinite(bike.latitude) || !Number.isFinite(bike.longitude)) return;

        activeBikeNumbers.add(bikeNumber);
        let marker = state.bikeMarkerMap[bikeNumber];
        if (!marker) {
            marker = L.circleMarker([bike.latitude, bike.longitude], {
                radius: 4,
                color: '#f07030',
                fillColor: '#f07030',
                fillOpacity: 1,
            }).addTo(map);
            state.bikeMarkerMap[bikeNumber] = marker;
        } else {
            marker.setLatLng([bike.latitude, bike.longitude]);
        }
        marker.bindPopup(createBikePopupContent(bike));
    });

    Object.entries(state.bikeMarkerMap).forEach(([bikeNumber, marker]) => {
        if (activeBikeNumbers.has(bikeNumber)) return;
        map.removeLayer(marker);
        delete state.bikeMarkerMap[bikeNumber];
    });
}

function createStationPopupContent(station) {
    const content = document.createElement('div');
    const heading = document.createElement('strong');
    heading.textContent = station.name || `Station ${station.station_number}`;
    content.appendChild(heading);

    const count = document.createElement('p');
    count.textContent = `Available bikes: ${station.bike_count}`;
    content.appendChild(count);

    const parking = document.createElement('p');
    parking.textContent = 'Free parking: unavailable';
    content.appendChild(parking);

    const typeCounts = Object.entries(station.bike_type_counts || {});
    if (typeCounts.length > 0) {
        const types = document.createElement('ul');
        typeCounts.forEach(([bikeType, amount]) => {
            const item = document.createElement('li');
            item.textContent = `Type ${bikeType}: ${amount}`;
            types.appendChild(item);
        });
        content.appendChild(types);
    }

    return content;
}

function createBikePopupContent(bike) {
    const content = document.createElement('div');
    content.textContent = `Bike ${bike.bike_number} | Type ${bike.bike_type || 'unknown'}`;
    return content;
}
