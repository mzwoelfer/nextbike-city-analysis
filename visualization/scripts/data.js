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
        const filePath = `data/${state.city_id}_trips_${state.date}.csv.gz`;
        const csvData = await fetchAndParseGzipCSV(filePath);
        console.log("LOADTRIPSDATA", csvData)

        state.tripsData = csvData.map(row => ({
            bike_number: row.bike_number,
            start_latitude: Number(row.start_latitude),
            start_longitude: Number(row.start_longitude),
            start_time: row.start_time,
            end_latitude: Number(row.end_latitude),
            end_longitude: Number(row.end_longitude),
            end_time: row.end_time,
            duration: Number(row.duration),
            date: row.date,
            distance: Number(row.distance),
            segments: JSON.parse(row.segments.replace(/'/g, '"')), // Convert stringified array to object
        }));
        
        // Centers on these city coordinates....
        // Get cities lat and long from somewhere else.
        state.city_lat = state.tripsData[0].start_latitude;
        state.city_lng = state.tripsData[0].start_longitude;

        console.log('Trips data loaded:', state.tripsData);
        return
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
        const filePath = `data/${state.city_id}_stations_${state.date}.csv.gz`;
        const csvData = await fetchAndParseGzipCSV(filePath);
        console.log("STATIONS:", csvData)

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

        console.log('Station data loaded:', state.stationData);
        return
    } catch (err) {
        console.error('Error loading station data:', err);
    }
};


export const checkTripsDataExists = async (date) => {
    /**
     * True if file exists.
     * Check if the csv.gz file for the date exists.
     */
    try {
        const response = await fetch(`data/${state.city_id}_trips_${date}.csv.gz`, { method: 'HEAD' });
        return response.ok;
    } catch (err) {
        console.error('Error checking trip data file:', err);
        return false;
    }
}
