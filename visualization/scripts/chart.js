// Pre-compute how many trips are active at each minute of the day
export function buildTripsPerMinute(tripsData) {
    const counts = new Int16Array(1441); // index = minute 0..1440
    tripsData.forEach(trip => {
        const startMin = minutesOf(new Date(trip.start_time));
        const endMin   = Math.min(minutesOf(new Date(trip.end_time)), 1440);
        for (let m = startMin; m <= endMin; m++) {
            counts[m]++;
        }
    });
    return counts;
}

function minutesOf(date) {
    return date.getHours() * 60 + date.getMinutes();
}

let _canvas       = null;
let _counts       = null;
let _lastMinute   = 0;

export function initChart(canvas, tripsPerMinute) {
    _canvas = canvas;
    _counts = tripsPerMinute;
    _draw(_lastMinute);
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
