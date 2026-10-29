import { minutesSinceMidnight } from './utils.js';

// Pre-compute how many trips are active at each minute of the day
export function buildTripsPerMinute(tripsData, timezone = null) {
    const tripCountsByMinute = new Int16Array(1441); // index = minute 0..1440
    tripsData.forEach(trip => {
        const startMinute = trip.start_minute_city ?? minutesSinceMidnight(new Date(trip.start_time), timezone);
        const endMinute = Math.min(trip.end_minute_city ?? minutesSinceMidnight(new Date(trip.end_time), timezone), 1440);
        for (let minute = startMinute; minute <= endMinute; minute++) {
            tripCountsByMinute[minute]++;
        }
    });
    return tripCountsByMinute;
}

let _canvas = null;
let _tripCountsByMinute = null;
let _lastMinute = 0;
let _onSeek = null;

export function initChart(canvas, tripsPerMinute, onSeek) {
    _canvas = canvas;
    _tripCountsByMinute = tripsPerMinute;
    _onSeek = onSeek || null;

    canvas.removeEventListener('click', _handleChartClick);
    canvas.addEventListener('click', _handleChartClick);

    _draw(_lastMinute);
}

function _handleChartClick(event) {
    if (!_onSeek || !_canvas) return;

    const chartBounds = _canvas.getBoundingClientRect();
    const paddingLeft = 36, paddingRight = 10;
    const contentWidth = chartBounds.width - paddingLeft - paddingRight;
    const clickOffsetX = Math.min(Math.max(event.clientX - chartBounds.left - paddingLeft, 0), contentWidth);

    _onSeek(Math.round((clickOffsetX / contentWidth) * 1440));
}

export function updateChartDot(currentMinute) {
    _lastMinute = currentMinute;
    if (!_canvas || !_tripCountsByMinute) return;
    _draw(currentMinute);
}

function _draw(currentMinute) {
    const canvas = _canvas;
    const tripCountsByMinute = _tripCountsByMinute;

    const devicePixelRatio = window.devicePixelRatio || 1;
    const chartBounds = canvas.getBoundingClientRect();

    if (chartBounds.width === 0 || chartBounds.height === 0) return;

    canvas.width = chartBounds.width * devicePixelRatio;
    canvas.height = chartBounds.height * devicePixelRatio;

    const context = canvas.getContext('2d');
    context.scale(devicePixelRatio, devicePixelRatio);

    const chartWidth = chartBounds.width;
    const chartHeight = chartBounds.height;

    const paddingLeft = 36, paddingRight = 10, paddingTop = 10, paddingBottom = 26;
    const contentWidth = chartWidth - paddingLeft - paddingRight;
    const contentHeight = chartHeight - paddingTop - paddingBottom;

    let maxCount = 1;
    for (let minute = 0; minute <= 1440; minute++) {
        if (tripCountsByMinute[minute] > maxCount) maxCount = tripCountsByMinute[minute];
    }

    const xForMinute = minute => paddingLeft + (minute / 1440) * contentWidth;
    const yForCount = count => paddingTop + contentHeight - (count / maxCount) * contentHeight;

    context.clearRect(0, 0, chartWidth, chartHeight);

    // ---- grid lines + y-axis labels ----
    const yAxisStepCount = 4;
    context.strokeStyle = 'rgba(240,240,240,0.1)';
    context.lineWidth = 1;
    context.fillStyle = 'rgba(240,240,240,0.4)';
    context.font = '9px sans-serif';
    context.textAlign = 'right';

    for (let step = 0; step <= yAxisStepCount; step++) {
        const stepValue = Math.round((maxCount / yAxisStepCount) * step);
        const y = yForCount(stepValue);

        context.beginPath();
        context.moveTo(paddingLeft, y);
        context.lineTo(paddingLeft + contentWidth, y);
        context.stroke();

        if (step > 0) context.fillText(stepValue, paddingLeft - 4, y + 3);
    }

    // ---- area fill ----
    context.beginPath();
    context.moveTo(xForMinute(0), yForCount(0));
    for (let minute = 0; minute <= 1440; minute++) {
        context.lineTo(xForMinute(minute), yForCount(tripCountsByMinute[minute]));
    }
    context.lineTo(xForMinute(1440), yForCount(0));
    context.closePath();
    context.fillStyle = 'rgba(240,112,48,0.18)';
    context.fill();

    // ---- line ----
    context.beginPath();
    context.moveTo(xForMinute(0), yForCount(tripCountsByMinute[0]));
    for (let minute = 1; minute <= 1440; minute++) {
        context.lineTo(xForMinute(minute), yForCount(tripCountsByMinute[minute]));
    }
    context.strokeStyle = '#f07030';
    context.lineWidth = 1.5;
    context.stroke();

    // ---- x-axis labels ----
    context.fillStyle = 'rgba(240,240,240,0.45)';
    context.font = '9px sans-serif';
    context.textAlign = 'center';
    [['00', 0], ['06', 360], ['12', 720], ['18', 1080], ['24', 1440]].forEach(([label, minute]) => {
        context.fillText(label, xForMinute(minute), chartHeight - 7);
    });

    // ---- current-time dot ----
    const clampedMinute = Math.min(Math.max(currentMinute, 0), 1440);
    const dotX = xForMinute(clampedMinute);
    const dotY = yForCount(tripCountsByMinute[clampedMinute]);

    context.beginPath();
    context.arc(dotX, dotY, 5, 0, Math.PI * 2);
    context.fillStyle = '#f07030';
    context.fill();
    context.strokeStyle = '#ffffff';
    context.lineWidth = 2;
    context.stroke();
}

// =============================================================================
// GENERIC HISTOGRAM  (shared by duration + distance)
// opts: { field, bucketSize, bucketCount, labels }
//   field       — key on each trip object  (string)
//   bucketSize  — width of each bucket in data units
//   bucketCount — total buckets incl. the overflow bucket
//   labels      — array[bucketCount] of x-axis strings (empty string = skip)
// =============================================================================
function _drawHistogram(canvas, tripsData, { field, valueFn, bucketSize, bucketCount, labels }) {
    if (!canvas || !tripsData || tripsData.length === 0) return;

    const getValue = valueFn || (trip => parseFloat(trip[field]));
    const tripCountsByBucket = new Int32Array(bucketCount);

    tripsData.forEach(trip => {
        const value = getValue(trip);
        if (isNaN(value) || value < 0) return;

        const bucketIndex = value >= (bucketCount - 1) * bucketSize
            ? bucketCount - 1
            : Math.floor(value / bucketSize);
        tripCountsByBucket[bucketIndex]++;
    });

    const devicePixelRatio = window.devicePixelRatio || 1;
    const chartBounds = canvas.getBoundingClientRect();
    if (chartBounds.width === 0 || chartBounds.height === 0) return;

    canvas.width = chartBounds.width * devicePixelRatio;
    canvas.height = chartBounds.height * devicePixelRatio;

    const context = canvas.getContext('2d');
    context.scale(devicePixelRatio, devicePixelRatio);

    const chartWidth = chartBounds.width;
    const chartHeight = chartBounds.height;

    const paddingLeft = 36, paddingRight = 8, paddingTop = 10, paddingBottom = 26;
    const contentWidth = chartWidth - paddingLeft - paddingRight;
    const contentHeight = chartHeight - paddingTop - paddingBottom;

    let maxCount = 1;
    for (let bucketIndex = 0; bucketIndex < bucketCount; bucketIndex++) {
        if (tripCountsByBucket[bucketIndex] > maxCount) maxCount = tripCountsByBucket[bucketIndex];
    }

    context.clearRect(0, 0, chartWidth, chartHeight);

    const barWidth = contentWidth / bucketCount;
    const barGap = Math.max(1, barWidth * 0.15);

    // ---- y-axis grid + labels ----
    context.strokeStyle = 'rgba(240,240,240,0.1)';
    context.lineWidth = 1;
    context.fillStyle = 'rgba(240,240,240,0.4)';
    context.font = '9px sans-serif';
    context.textAlign = 'right';

    const yAxisStepCount = 4;
    for (let step = 0; step <= yAxisStepCount; step++) {
        const stepValue = Math.round((maxCount / yAxisStepCount) * step);
        const y = paddingTop + contentHeight - (stepValue / maxCount) * contentHeight;

        context.beginPath();
        context.moveTo(paddingLeft, y);
        context.lineTo(paddingLeft + contentWidth, y);
        context.stroke();

        if (step > 0) context.fillText(stepValue, paddingLeft - 4, y + 3);
    }

    // ---- bars ----
    for (let bucketIndex = 0; bucketIndex < bucketCount; bucketIndex++) {
        const barX = paddingLeft + bucketIndex * barWidth + barGap / 2;
        const barHeight = (tripCountsByBucket[bucketIndex] / maxCount) * contentHeight;
        const barY = paddingTop + contentHeight - barHeight;

        context.fillStyle = 'rgba(240,112,48,0.75)';
        context.fillRect(barX, barY, barWidth - barGap, barHeight);
    }

    // ---- x-axis labels ----
    context.fillStyle = 'rgba(240,240,240,0.45)';
    context.font = '9px sans-serif';
    context.textAlign = 'center';
    for (let bucketIndex = 0; bucketIndex < bucketCount; bucketIndex++) {
        if (!labels[bucketIndex]) continue;
        context.fillText(labels[bucketIndex], paddingLeft + bucketIndex * barWidth + barWidth / 2, chartHeight - 7);
    }
}

// -- Duration: 5-min buckets, 0-5 ... 55-60, 60+ ------------------------------
export function drawDurationHistogram(canvas, tripsData) {
    const bucketSize = 5;
    const bucketCount = 13;
    const labels = Array.from({ length: bucketCount }, (_, bucketIndex) =>
        bucketIndex === bucketCount - 1 ? '60+' : String(bucketIndex * bucketSize)
    );

    _drawHistogram(canvas, tripsData, {
        valueFn: trip => trip.duration / 60,   // convert seconds to minutes
        bucketSize, bucketCount, labels,
    });
}

// -- Distance: 500-m buckets, 0-500 ... 5500-6000, 6000+ ----------------------
export function drawDistanceHistogram(canvas, tripsData) {
    const bucketSize = 500;
    const bucketCount = 13;
    // Show every other label to avoid crowding (0, 1k, 2k ... 6k+)
    const labels = Array.from({ length: bucketCount }, (_, bucketIndex) => {
        if (bucketIndex === bucketCount - 1) return '6k+';
        const kilometers = (bucketIndex * bucketSize) / 1000;
        return bucketIndex % 2 === 0 ? (kilometers === 0 ? '0' : kilometers + 'k') : '';
    });

    _drawHistogram(canvas, tripsData, { field: 'distance', bucketSize, bucketCount, labels });
}

export function drawHourHistogram(canvas, tripsData, timezone = null) {
    const bucketCount = 24;
    const labels = Array.from({ length: 24 }, (_, hour) => hour % 3 === 0 ? String(hour) : '');

    _drawHistogram(canvas, tripsData, {
        valueFn: trip => Math.floor((trip.start_minute_city ?? minutesSinceMidnight(new Date(trip.start_time), timezone)) / 60),
        bucketSize: 1,
        bucketCount,
        labels,
    });
}