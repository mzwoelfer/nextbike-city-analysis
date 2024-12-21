import state from './state.js';
import { initializeMap, plotStationsOnMap } from './map.js';

export const loadTripsData = async () => {
    try {
        const response = await fetch(`data/${state.city_id}_trips_2024-12-20.json`);
        const data = await response.json();

        state.tripsData = data.trips;
        state.city_lat = data.city_info.lat;
        state.city_lng = data.city_info.lng;

        initializeMap(state.city_lat, state.city_lng);
        console.log('Trips data loaded:', state.tripsData);
    } catch (err) {
        console.error('Error loading trip data:', err);
    }
};

export const loadStationData = async () => {
    try {
        const response = await fetch(`data/${state.city_id}_stations_2024-12-20.json`);
        state.stationData = await response.json();

        plotStationsOnMap();
        console.log('Station data loaded:', state.stationData);
    } catch (err) {
        console.error('Error loading station data:', err);
    }
};
