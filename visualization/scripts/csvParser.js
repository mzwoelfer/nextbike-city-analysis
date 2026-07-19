/**
 * Parse CSV text into an array of row objects.
 * @param {string} csvText - Raw CSV text.
 * @returns {Array<Object>} Parsed rows.
 */
export function parseCsvText(csvText) {
  const lines = csvText.trim().split("\n");
  const headers = lines[0].split(",");

  return lines.slice(1).map((line) => parseCsvLine(line, headers));
}

/**
 * Parse one CSV line into a row object, respecting quoted fields.
 * @param {string} line - Raw CSV line.
 * @param {string[]} headers - Column headers, in order.
 * @returns {Object} One row keyed by header.
 */
function parseCsvLine(line, headers) {
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
}

/**
 * Fetch and parse a gzipped CSV file.
 * @param {string} filePath - Relative path to the .csv.gz file.
 * @returns {Promise<Array<Object>>} Parsed row objects.
 */
export async function fetchAndParseGzipCsv(filePath) {
  const response = await fetch(filePath);
  if (!response.ok) {
    throw new Error(`Failed to load ${filePath}`);
  }

  const decompressedStream = response.body.pipeThrough(new DecompressionStream("gzip"));
  const csvText = await new Response(decompressedStream).text();
  return parseCsvText(csvText);
}