import state from './state.js';


/**
 * Parse CSV string to array of objects
 * @param {string} csvText - CSV text.
 * @returns {Array<Object>}
 */
const parseCSV = async (csvText) => {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',');

    // Rawdogging CSV parsing... in the name of personal improvement
    return lines.slice(1).map(line => {
        const values = [];
        let current = '';
        let insideQuotes = false;

        for (let char of line) {
            if (char === '"' && insideQuotes){
                insideQuotes = false;
            } else if (char === '"' && !insideQuotes) {
                insideQuotes = true;
            } else if (char === ',' && !insideQuotes){
                values.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        values.push(current.trim());

        return headers.reduce((acc, header, index) => {
            acc[header] = values[index];
            return acc;
        }, {});
    });
};


export const loadAvailableFiles = async () => {
    /**
     * Load available files either from:
     * - /api/available (production docker mode - uses database)
     * - manifest.json file (if it exists)
     * - or the directory listing from the server.
     */
    let groupedFiles = {};

    // Try the database API first (production mode)
    try {
        const response = await fetch('/api/available');
        if (response.ok) {
            const data = await response.json();
            data.forEach(({ city_id, city_name, dates }) => {
                groupedFiles[city_id] = dates;
                state.cities[city_name] = city_id;
            });
            state.useApi = true;
            console.log('Loaded available data from API:', groupedFiles);
            return groupedFiles;
        }
    } catch {}

    // Fall back to static file discovery (GitHub Pages / plain http.server mode)
    state.useApi = false;

    try {
        const response = await fetch('data/manifest.json');
        if (!response.ok) {
            throw new Error("Manifest file not found");
        }
        const files = await response.json();

        files.forEach(file => {
            const match = file.match(/(\d+)_stations_(\d{4}-\d{2}-\d{2})\.csv.gz/);
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
                .filter(file => file.endsWith('.csv.gz'));

            files.forEach(file => {
                const match = file.match(/(\d+)_stations_(\d{4}-\d{2}-\d{2})\.csv.gz/);
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


/**
 * Fetch and parse gzipped CSV file.
 * @param {string} filePath - Path to .csv.gz file
 * @returns {Promise<Array<Object>>}
 */
const fetchAndParseGzipCSV = async (filePath) => {
    try {
        const response = await fetch(filePath);
        if (!response.ok) throw new Error (`Failed to load ${filePath}`)
        
        const decompressedStream = response.body.pipeThrough(new DecompressionStream('gzip'));
        const text = await new Response(decompressedStream).text();
        const parsedCSV = await parseCSV(text);
        return parsedCSV;
    } catch (err) {
        console.error(`ERROR: Loading CSV file ${filePath}`, err);
        return [];
    }
}

export const loadFirstAvailableData = async () => {
    const city_ids = Object.keys(state.availableFiles);
    const first_city_id = city_ids[0];
    state.city_id = first_city_id;
    state.date = state.availableFiles[first_city_id][0];

    if (state.useApi) {
        // city names already populated from /api/available
        return;
    }

    // existing CSV fallback for static / GitHub Pages mode
    const cityPromises = city_ids.map(async (city_id) => {
        const stationData = await fetchAndParseGzipCSV(`data/${city_id}_stations_${state.date}.csv.gz`);
        console.log("RESPONSE:", stationData)
        const city_name = stationData[0]["city_name"]
        return { city_name, city_id };
    })

    const cities = await Promise.all(cityPromises);

    cities.forEach(({ city_name, city_id }) => {
        state.cities[city_name] = city_id;
    })
}

/**
 * Load trips and convert it to the original JSON format
 * @returns {Promise<Array<Trip>>}
 */
export const loadTripsData = async () => {
    try {
        if (state.useApi) {
            const response = await fetch(`/api/trips?city_id=${state.city_id}&date=${state.date}`);
            if (!response.ok) throw new Error(`API request failed for trips ${state.city_id} ${state.date}`);
            const geojson = await response.json();

            state.tripsData = geojson.features.map(feature => ({
                bike_number: feature.properties.bike_number,
                start_time: feature.properties.start_time,
                end_time: feature.properties.end_time,
                duration: feature.properties.duration,
                distance: feature.properties.distance,
                coordinates: feature.geometry.coordinates,  // [[lon, lat], ...]
                timestamps: feature.properties.timestamps,
            }));

            state.city_lat = state.tripsData[0].coordinates[0][1];
            state.city_lng = state.tripsData[0].coordinates[0][0];
        } else {
            const rows = await fetchAndParseGzipCSV(`data/${state.city_id}_trips_${state.date}.csv.gz`);
            if (!rows.length) throw new Error(`No trip data for city ${state.city_id} on ${state.date}`);
            state.tripsData = rows.map(row => {
                // segments is a Python-repr list: [[lat, lon, 'timestamp'], ...]
                const segments = JSON.parse(row.segments.replace(/'/g, '"'));
                return {
                    bike_number: row.bike_number,
                    start_time: row.start_time,
                    end_time: row.end_time,
                    duration: Number(row.duration),
                    distance: Number(row.distance),
                    coordinates: segments.map(([lat, lon]) => [lon, lat]),  // GeoJSON: [lon, lat]
                    timestamps: segments.map(([,, ts]) => ts),
                };
            });
            state.city_lat = state.tripsData[0].coordinates[0][1];
            state.city_lng = state.tripsData[0].coordinates[0][0];
        }

        console.log('Trips data loaded:', state.tripsData);
        return;
    } catch (err) {
        console.error('Error loading trip data:', err);
    }
};

/**
 * Load station data and convert to match the original JSON format
 * @returns {Promise<Array<Station>>}
 */
export const loadStationData = async () => {
    try {
        let rows;

        if (state.useApi) {
            const response = await fetch(`/api/stations?city_id=${state.city_id}&date=${state.date}`);
            if (!response.ok) throw new Error(`API request failed for stations ${state.city_id} ${state.date}`);
            rows = await response.json();
            state.stationData = rows.map(row => ({
                minute: row.minute,
                id: row.id,
                uid: row.uid,
                latitude: row.latitude,
                longitude: row.longitude,
                name: row.name,
                spot: row.spot,
                station_number: row.station_number,
                maintenance: row.maintenance,
                terminal_type: row.terminal_type,
                city_id: row.city_id,
                city_name: row.city_name,
                bike_count: row.bike_count,
                bike_list: row.bike_list || "",
            }));
        } else {
            const filePath = `data/${state.city_id}_stations_${state.date}.csv.gz`;
            const csvData = await fetchAndParseGzipCSV(filePath);
            state.stationData = csvData.map(row => ({
                minute: row.minute,
                id: Number(row.id),
                uid: Number(row.uid),
                latitude: Number(row.latitude),
                longitude: Number(row.longitude),
                name: row.name,
                spot: row.spot === "True",
                station_number: Number(row.station_number),
                maintenance: row.maintenance === "True",
                terminal_type: row.terminal_type,
                city_id: Number(row.city_id),
                city_name: row.city_name,
                bike_count: Number(row.bike_count),
                bike_list: row.bike_list || "",
            }));
        }

        console.log('Station data loaded:', state.stationData);
        return;
    } catch (err) {
        console.error('Error loading station data:', err);
    }
};


export const checkTripsDataExists = async (date) => {
    if (state.useApi) {
        return state.availableFiles[state.city_id]?.includes(date) ?? false;
    }
    try {
        const response = await fetch(`data/${state.city_id}_trips_${date}.geojson.gz`, { method: 'HEAD' });
        return response.ok;
    } catch (err) {
        console.error('Error checking trip data file:', err);
        return false;
    }
}
