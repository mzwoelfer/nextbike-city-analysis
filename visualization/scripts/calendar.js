import state from './state.js';

const MONTHS = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
];

let _onDateSelect = null;
let _calYear      = null;
let _calMonth     = null;
let _isOpen       = false;

export function initCalendar(onDateSelect) {
    _onDateSelect = onDateSelect;

    const trigger = document.getElementById('trip-date');
    trigger.classList.add('calendar-trigger');
    trigger.title = 'Click to pick a date';
    trigger.addEventListener('click', _toggleCalendar);

    document.addEventListener('click', (e) => {
        if (_isOpen &&
            !e.target.closest('#date-picker') &&
            !e.target.closest('#trip-date')) {
            _closeCalendar();
        }
    });

    document.getElementById('cal-prev-month').addEventListener('click', (e) => {
        e.stopPropagation();
        _calMonth--;
        if (_calMonth < 0) { _calMonth = 11; _calYear--; }
        _renderCalendar();
    });

    document.getElementById('cal-next-month').addEventListener('click', (e) => {
        e.stopPropagation();
        _calMonth++;
        if (_calMonth > 11) { _calMonth = 0; _calYear++; }
        _renderCalendar();
    });
}

// Called by main.js whenever the city changes so the calendar shows fresh dates
export function refreshCalendar() {
    if (_isOpen) _renderCalendar();
}

function _toggleCalendar(e) {
    e.stopPropagation();
    _isOpen ? _closeCalendar() : _openCalendar();
}

function _openCalendar() {
    const d = new Date((state.date || new Date().toISOString().split('T')[0]) + 'T00:00:00');
    _calYear  = d.getFullYear();
    _calMonth = d.getMonth();
    _renderCalendar();
    document.getElementById('date-picker').hidden = false;
    _isOpen = true;
}

function _closeCalendar() {
    document.getElementById('date-picker').hidden = true;
    _isOpen = false;
}

function _availableDates() {
    const files = state.availableFiles[state.city_id];
    return new Set(Array.isArray(files) ? files : []);
}

function _renderCalendar() {
    document.getElementById('cal-month-label').textContent =
        `${MONTHS[_calMonth]} ${_calYear}`;

    const available   = _availableDates();
    const firstDay    = new Date(_calYear, _calMonth, 1).getDay(); // 0=Sun
    const daysInMonth = new Date(_calYear, _calMonth + 1, 0).getDate();

    const grid = document.getElementById('cal-days');
    grid.innerHTML = '';

    // Leading empty cells so day 1 lands on the right weekday column
    for (let i = 0; i < firstDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'cal-day cal-day-empty';
        grid.appendChild(empty);
    }

    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${_calYear}-${String(_calMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const hasData    = available.has(dateStr);
        const isSelected = dateStr === state.date;

        const cell = document.createElement('div');
        cell.textContent = d;
        cell.className   = 'cal-day' +
            (hasData    ? ' cal-day-available'   : ' cal-day-unavailable') +
            (isSelected ? ' cal-day-selected'    : '');

        if (hasData) {
            cell.addEventListener('click', (e) => {
                e.stopPropagation();
                _closeCalendar();
                _onDateSelect(dateStr);
            });
        }

        grid.appendChild(cell);
    }
}
