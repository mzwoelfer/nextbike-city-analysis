import { minutesSinceMidnight } from './utils.js';

// Pre-compute how many trips are active at each minute of the day
export function buildTripsPerMinute(tripsData, timezone = null) {
    const counts = new Int16Array(1441); // index = minute 0..1440
    tripsData.forEach(trip => {
        const startMin = trip.start_minute_city ?? minutesSinceMidnight(new Date(trip.start_time), timezone);
        const endMin   = Math.min(trip.end_minute_city ?? minutesSinceMidnight(new Date(trip.end_time), timezone), 1440);
        for (let m = startMin; m <= endMin; m++) {
            counts[m]++;
        }
    });
    return counts;
}

let _canvas       = null;
let _counts       = null;
let _lastMinute   = 0;
let _onSeek       = null;

export function initChart(canvas, tripsPerMinute, onSeek) {
    _canvas = canvas;
    _counts = tripsPerMinute;
    _onSeek = onSeek || null;
    canvas.removeEventListener('click', _handleChartClick);
    canvas.addEventListener('click', _handleChartClick);
    _draw(_lastMinute);
}

function _handleChartClick(e) {
    if (!_onSeek || !_canvas) return;
    const rect = _canvas.getBoundingClientRect();
    const padL = 36, padR = 10;
    const cW   = rect.width - padL - padR;
    const x    = Math.min(Math.max(e.clientX - rect.left - padL, 0), cW);
    _onSeek(Math.round((x / cW) * 1440));
}

export function updateChartDot(currentMinute) {
    _lastMinute = currentMinute;
    if (!_canvas || !_counts) return;
    _draw(currentMinute);
}

function _draw(currentMinute) {
    const canvas = _canvas;
    const counts = _counts;

    const dpr  = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    if (rect.width === 0 || rect.height === 0) return;

    canvas.width  = rect.width  * dpr;
    canvas.height = rect.height * dpr;

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const W = rect.width;
    const H = rect.height;

    const padL = 36, padR = 10, padT = 10, padB = 26;
    const cW   = W - padL - padR;
    const cH   = H - padT - padB;

    let max = 1;
    for (let m = 0; m <= 1440; m++) { if (counts[m] > max) max = counts[m]; }

    const xAt = m => padL + (m / 1440) * cW;
    const yAt = v => padT + cH - (v / max) * cH;

    ctx.clearRect(0, 0, W, H);

    // ---- grid lines + y-axis labels ----
    const ySteps = 4;
    ctx.strokeStyle = 'rgba(240,240,240,0.1)';
    ctx.lineWidth   = 1;
    ctx.fillStyle   = 'rgba(240,240,240,0.4)';
    ctx.font        = '9px sans-serif';
    ctx.textAlign   = 'right';
    for (let i = 0; i <= ySteps; i++) {
        const v = Math.round((max / ySteps) * i);
        const y = yAt(v);
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(padL + cW, y);
        ctx.stroke();
        if (i > 0) ctx.fillText(v, padL - 4, y + 3);
    }

    // ---- area fill ----
    ctx.beginPath();
    ctx.moveTo(xAt(0), yAt(0));
    for (let m = 0; m <= 1440; m++) ctx.lineTo(xAt(m), yAt(counts[m]));
    ctx.lineTo(xAt(1440), yAt(0));
    ctx.closePath();
    ctx.fillStyle = 'rgba(240,112,48,0.18)';
    ctx.fill();

    // ---- line ----
    ctx.beginPath();
    ctx.moveTo(xAt(0), yAt(counts[0]));
    for (let m = 1; m <= 1440; m++) ctx.lineTo(xAt(m), yAt(counts[m]));
    ctx.strokeStyle = '#f07030';
    ctx.lineWidth   = 1.5;
    ctx.stroke();

    // ---- x-axis labels ----
    ctx.fillStyle  = 'rgba(240,240,240,0.45)';
    ctx.font       = '9px sans-serif';
    ctx.textAlign  = 'center';
    [['00', 0], ['06', 360], ['12', 720], ['18', 1080], ['24', 1440]].forEach(([lbl, m]) => {
        ctx.fillText(lbl, xAt(m), H - 7);
    });

    // ---- current-time dot ----
    const cm = Math.min(Math.max(currentMinute, 0), 1440);
    const dx = xAt(cm);
    const dy = yAt(counts[cm]);
    ctx.beginPath();
    ctx.arc(dx, dy, 5, 0, Math.PI * 2);
    ctx.fillStyle   = '#f07030';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth   = 2;
    ctx.stroke();
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
    const buckets = new Int32Array(bucketCount);
    tripsData.forEach(trip => {
        const val = getValue(trip);
        if (isNaN(val) || val < 0) return;
        const idx = val >= (bucketCount - 1) * bucketSize
            ? bucketCount - 1
            : Math.floor(val / bucketSize);
        buckets[idx]++;
    });

    const dpr  = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    canvas.width  = rect.width  * dpr;
    canvas.height = rect.height * dpr;

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const W = rect.width;
    const H = rect.height;

    const padL = 36, padR = 8, padT = 10, padB = 26;
    const cW   = W - padL - padR;
    const cH   = H - padT - padB;

    let maxVal = 1;
    for (let i = 0; i < bucketCount; i++) if (buckets[i] > maxVal) maxVal = buckets[i];

    ctx.clearRect(0, 0, W, H);

    const barW = cW / bucketCount;
    const gap  = Math.max(1, barW * 0.15);

    // ---- y-axis grid + labels ----
    ctx.strokeStyle = 'rgba(240,240,240,0.1)';
    ctx.lineWidth   = 1;
    ctx.fillStyle   = 'rgba(240,240,240,0.4)';
    ctx.font        = '9px sans-serif';
    ctx.textAlign   = 'right';
    const ySteps = 4;
    for (let i = 0; i <= ySteps; i++) {
        const v = Math.round((maxVal / ySteps) * i);
        const y = padT + cH - (v / maxVal) * cH;
        ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + cW, y); ctx.stroke();
        if (i > 0) ctx.fillText(v, padL - 4, y + 3);
    }

    // ---- bars ----
    for (let i = 0; i < bucketCount; i++) {
        const x  = padL + i * barW + gap / 2;
        const bH = (buckets[i] / maxVal) * cH;
        const y  = padT + cH - bH;
        ctx.fillStyle = 'rgba(240,112,48,0.75)';
        ctx.fillRect(x, y, barW - gap, bH);
    }

    // ---- x-axis labels ----
    ctx.fillStyle = 'rgba(240,240,240,0.45)';
    ctx.font      = '9px sans-serif';
    ctx.textAlign = 'center';
    for (let i = 0; i < bucketCount; i++) {
        if (!labels[i]) continue;
        ctx.fillText(labels[i], padL + i * barW + barW / 2, H - 7);
    }
}

// -- Duration: 5-min buckets, 0-5 … 55-60, 60+ --------------------------------
export function drawDurationHistogram(canvas, tripsData) {
    const bucketSize  = 5;
    const bucketCount = 13;
    const labels = Array.from({ length: bucketCount }, (_, i) =>
        i === bucketCount - 1 ? '60+' : String(i * bucketSize)
    );
    _drawHistogram(canvas, tripsData, {
        valueFn: trip => trip.duration / 60,   // convert seconds to minutes
        bucketSize, bucketCount, labels,
    });
}

// -- Distance: 500-m buckets, 0-500 … 5500-6000, 6000+ -----------------------
export function drawDistanceHistogram(canvas, tripsData) {
    const bucketSize  = 500;
    const bucketCount = 13;
    // Show every other label to avoid crowding (0, 1k, 2k … 6k+)
    const labels = Array.from({ length: bucketCount }, (_, i) => {
        if (i === bucketCount - 1) return '6k+';
        const km = (i * bucketSize) / 1000;
        return i % 2 === 0 ? (km === 0 ? '0' : km + 'k') : '';
    });
    _drawHistogram(canvas, tripsData, { field: 'distance', bucketSize, bucketCount, labels });
}

export function drawHourHistogram(canvas, tripsData, timezone = null) {
    const bucketCount = 24;
    const labels = Array.from({ length: 24 }, (_, i) => i % 3 === 0 ? String(i) : '');
    _drawHistogram(canvas, tripsData, {
        valueFn:    trip => Math.floor((trip.start_minute_city ?? minutesSinceMidnight(new Date(trip.start_time), timezone)) / 60),
        bucketSize: 1,
        bucketCount,
        labels,
    });
}