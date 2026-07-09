/**
 * Parse CSV text into an array of row objects.
 * @param {string} csvText - Raw CSV text.
 * @returns {Promise<Array<Object>>} Parsed rows.
 */
async function parseCsvText(csvText) {
  const lines = csvText.trim().split("\n");
  const headers = lines[0].split(",");

  return lines.slice(1).map((line) => {
    const values = [];
    let currentValue = "";
    let insideQuotes = false;

    for (const character of line) {
      if (character === '"' && insideQuotes) {
        insideQuotes = false;
      } else if (character === '"' && !insideQuotes) {
        insideQuotes = true;
      } else if (character === "," && !insideQuotes) {
        values.push(currentValue.trim());
        currentValue = "";
      } else {
        currentValue += character;
      }
    }

    values.push(currentValue.trim());

    return headers.reduce((row, header, index) => {
      row[header] = values[index];
      return row;
    }, {});
  });
}

/**
 * Fetch and parse a gzipped CSV file.
 * @param {string} filePath - Relative path to the .csv.gz file.
 * @returns {Promise<Array<Object>>} Parsed row objects.
 */
async function fetchAndParseGzipCsv(filePath) {
  const response = await fetch(filePath);
  if (!response.ok) {
    throw new Error(`Failed to load ${filePath}`);
  }

  const decompressedStream = response.body.pipeThrough(
    new DecompressionStream("gzip"),
  );
  const csvText = await new Response(decompressedStream).text();
  return parseCsvText(csvText);
}

/**
 * Group static station file names by city and date.
 * @param {string[]} fileNames - Station file names.
 * @returns {Object<string, string[]>} Dates grouped by city id.
 */
function groupStationFilesByCityAndDate(fileNames) {
  const availableFiles = {};

  fileNames.forEach((fileName) => {
    const match = fileName.match(/(\d+)_stations_(\d{4}-\d{2}-\d{2})\.csv\.gz/);
    if (!match) {
      return;
    }

    const [, cityId, availableDate] = match;
    if (!availableFiles[cityId]) {
      availableFiles[cityId] = [];
    }
    availableFiles[cityId].push(availableDate);
  });

  return availableFiles;
}

/**
 * Load available trip dates from manifest.json.
 * @returns {Promise<Object<string, string[]>>} Grouped dates.
 */
export async function loadAvailableDatesFromManifest() {
  const response = await fetch("data/manifest.json");
  if (!response.ok) {
    throw new Error("Manifest file not found");
  }

  const fileNames = await response.json();
  return groupStationFilesByCityAndDate(fileNames);
}

/**
 * Load available trip dates from the directory listing fallback.
 * @returns {Promise<Object<string, string[]>>} Grouped dates.
 */
export async function loadAvailableDatesFromDirectoryListing() {
  const response = await fetch("data/");
  const html = await response.text();
  const parser = new DOMParser();
  const documentBody = parser.parseFromString(html, "text/html");
  const fileNames = Array.from(documentBody.querySelectorAll("a"))
    .map((link) => link.getAttribute("href"))
    .filter((fileName) => fileName.endsWith(".csv.gz"));

  return groupStationFilesByCityAndDate(fileNames);
}

/**
 * Load city names from static station exports.
 * @param {string[]} cityIds - Available city ids.
 * @param {string} selectedDate - Date used to read station files.
 * @returns {Promise<Array<{ cityId: string, cityName: string | undefined }>>} Static city records.
 */
export async function loadStaticCityRecords(cityIds, selectedDate) {
  return Promise.all(
    cityIds.map(async (cityId) => {
      const stationRows = await fetchAndParseGzipCsv(
        `data/${cityId}_stations_${selectedDate}.csv.gz`,
      );
      return {
        cityId,
        cityName: stationRows[0]?.city_name,
      };
    }),
  );
}

/**
 * Load static trip rows from the generated CSV export.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<Array<Object>>} Parsed trip rows.
 */
export async function loadStaticTripRows(cityId, selectedDate) {
  return fetchAndParseGzipCsv(`data/${cityId}_trips_${selectedDate}.csv.gz`);
}

/**
 * Load static station rows from the generated CSV export.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Selected date.
 * @returns {Promise<Array<Object>>} Parsed station rows.
 */
export async function loadStaticStationRows(cityId, selectedDate) {
  return fetchAndParseGzipCsv(`data/${cityId}_stations_${selectedDate}.csv.gz`);
}

/**
 * Check whether a static trip file exists for the selected date.
 * @param {string|number} cityId - Selected city id.
 * @param {string} selectedDate - Date to check.
 * @returns {Promise<boolean>} True when the static trip file exists.
 */
export async function checkStaticTripDataExists(cityId, selectedDate) {
  const response = await fetch(
    `data/${cityId}_trips_${selectedDate}.geojson.gz`,
    { method: "HEAD" },
  );
  return response.ok;
}