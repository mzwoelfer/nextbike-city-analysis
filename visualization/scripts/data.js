import state from './state.js';


export const loadAvailableFiles = async () => {
    /**
     * Load available files either from:
     * - manifest.json file (if it exists)
     * - or the directory listing from the server.
     */
    let groupedFiles = {};

    try {
        const response = await fetch('data/manifest.json');
        if (!response.ok) {
            throw new Error("Manifest file not found");
        }
        const files = await response.json();

        files.forEach(file => {
            const match = file.match(/(\d+)_stations_(\d{4}-\d{2}-\d{2})\.json/);
            if (match) {
                const [_, cityId, date] = match;
                if (!groupedFiles[cityId]) {
                    groupedFiles[cityId] = [];
                }
                groupedFiles[cityId].push(date);
            }
        });

        console.log('Loaded files from manifest:', groupedFiles);
        return groupedFiles;
    } catch (err) {
        console.warn('Manifest.json not found or failed to load. Falling back to server-based file fetching:', err);

        try {
            const response = await fetch('data/');
            const html = await response.text();

            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const files = Array.from(doc.querySelectorAll('a'))
                .map(link => link.getAttribute('href'))
                .filter(file => file.endsWith('.json'));

            files.forEach(file => {
                const match = file.match(/(\d+)_stations_(\d{4}-\d{2}-\d{2})\.json/);
                if (match) {
                    const [_, cityId, date] = match;
                    if (!groupedFiles[cityId]) {
                        groupedFiles[cityId] = [];
                    }
                    groupedFiles[cityId].push(date);
                }
            });

            console.log('Loaded files from server directory:', groupedFiles);
        } catch (dirErr) {
            console.error('Failed to fetch directory listing as fallback:', dirErr);
        }
    }

    return groupedFiles;
};

export const loadFirstAvailableData = async () => {
    const city_ids = Object.keys(state.availableFiles);
    const first_city_id = city_ids[0];
    state.city_id = first_city_id;
    state.date = state.availableFiles[first_city_id][0];

    const cityPromises = city_ids.map(async (city_id) => {
        const response = await fetch(`data/${city_id}_stations_${state.date}.json`);
        const stationData = await response.json();
        const city_name = stationData[0]["city_name"]
        return { city_name, city_id };
    })

    const cities = await Promise.all(cityPromises);

    cities.forEach(({ city_name, city_id }) => {
        state.cities[city_name] = city_id;
    })
}

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
