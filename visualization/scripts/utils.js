
const minuteFormatterCache = new Map();
const timeFormatterCache = new Map();

const getMinuteFormatter = (timezone) => {
    if (!minuteFormatterCache.has(timezone)) {
        minuteFormatterCache.set(
            timezone,
            new Intl.DateTimeFormat('en-GB', {
                timeZone: timezone,
                hour: '2-digit',
                minute: '2-digit',
                hourCycle: 'h23',
            }),
        );
    }
    return minuteFormatterCache.get(timezone);
};

const getTimeFormatter = (timezone) => {
    if (!timeFormatterCache.has(timezone)) {
        timeFormatterCache.set(
            timezone,
            new Intl.DateTimeFormat('en-GB', {
                timeZone: timezone,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hourCycle: 'h23',
            }),
        );
    }
    return timeFormatterCache.get(timezone);
};

export const formatTime = (minutes) => {
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
};


export const minutesSinceMidnight = (date, timezone = null) => {
    if (!timezone) {
        return date.getHours() * 60 + date.getMinutes();
    }

    const parts = getMinuteFormatter(timezone).formatToParts(date);

    const hour = Number(parts.find((part) => part.type === "hour")?.value ?? "0");
    const minute = Number(parts.find((part) => part.type === "minute")?.value ?? "0");
    return hour * 60 + minute;
};


export const formatTimeInTimezone = (dateString, timezone) => {
    return getTimeFormatter(timezone).format(new Date(dateString));
};

/**
 * Fetch and parse a gzipped CSV file.
 * @param {string} filePath - Relative path to the .csv.gz file.
 * @returns {Promise<Array<Object>>} Parsed row objects.
 */
const fetchAndParseGzipCSV = async (filePath) => {
  try {
    const response = await fetch(filePath);
    if (!response.ok) throw new Error(`Failed to load ${filePath}`);

    const decompressedStream = response.body.pipeThrough(
      new DecompressionStream("gzip"),
    );
    const text = await new Response(decompressedStream).text();
    const parsedCSV = await parseCSV(text);
    return parsedCSV;
  } catch (err) {
    console.error(`ERROR: Loading CSV file ${filePath}`, err);
    return [];
  }
};


/**
 * Parse CSV text into an array of row objects.
 * @param {string} csvText - Raw CSV text.
 * @returns {Promise<Array<Object>>} Parsed rows.
 */
const parseCSV = async (csvText) => {
  const lines = csvText.trim().split("\n");
  const headers = lines[0].split(",");

  // Rawdogging CSV parsing... in the name of personal improvement
  return lines.slice(1).map((line) => {
    const values = [];
    let current = "";
    let insideQuotes = false;

    for (let char of line) {
      if (char === '"' && insideQuotes) {
        insideQuotes = false;
      } else if (char === '"' && !insideQuotes) {
        insideQuotes = true;
      } else if (char === "," && !insideQuotes) {
        values.push(current.trim());
        current = "";
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