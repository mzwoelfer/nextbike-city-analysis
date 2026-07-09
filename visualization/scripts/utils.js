
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
