import state from './state.js';

export const loadTripsData = async () => {
    /**
     * Loads a JSON file with the trips data into the state
     */
    try {
        const response = await fetch(`data/${state.city_id}_trips_${state.date}.json`);
        const data = await response.json();

        state.tripsData = data.trips;
        state.city_lat = data.city_info.lat;
        state.city_lng = data.city_info.lng;

        console.log('Trips data loaded:', state.tripsData);
        return
    } catch (err) {
        console.error('Error loading trip data:', err);
    }
};

export const loadStationData = async () => {
    /**
     * Loads a JSON file with the station data into the state
     */
    try {
        const response = await fetch(`data/${state.city_id}_stations_${state.date}.json`);
        state.stationData = await response.json();

        console.log('Station data loaded:', state.stationData);
        return
    } catch (err) {
        console.error('Error loading station data:', err);
    }
};


export const checkTripsDataExists = async (date) => {
    /**
     * True if file exists.
     * Check if the JSON file for the date exists.
     */
    try {
        const response = await fetch(`data/${state.city_id}_trips_${date}.json`, { method: 'HEAD' });
        return response.ok;
    } catch (err) {
        console.error('Error checking trip data file:', err);
        return false;
    }
}