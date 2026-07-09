import state from './state.js';

const MONTHS = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
];

let _onDateSelect  = null;
let _calendarYear  = null;
let _calendarMonth = null;
let _isOpen        = false;

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
        _calendarMonth--;
        if (_calendarMonth < 0) { _calendarMonth = 11; _calendarYear--; }
        _renderCalendar();
    });

    document.getElementById('cal-next-month').addEventListener('click', (e) => {
        e.stopPropagation();
        _calendarMonth++;
        if (_calendarMonth > 11) { _calendarMonth = 0; _calendarYear++; }
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
    const todayDateString    = new Date().toISOString().split('T')[0];
    const selectedDateString = state.date || todayDateString;
    const selectedDate       = new Date(selectedDateString + 'T00:00:00');

    _calendarYear  = selectedDate.getFullYear();
    _calendarMonth = selectedDate.getMonth();

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
        `${MONTHS[_calendarMonth]} ${_calendarYear}`;

    const available   = _availableDates();
    const firstWeekday = new Date(_calendarYear, _calendarMonth, 1).getDay(); // 0=Sun
    const daysInMonth  = new Date(_calendarYear, _calendarMonth + 1, 0).getDate();

    const grid = document.getElementById('cal-days');
    grid.innerHTML = '';

    // Leading empty cells so day 1 lands on the right weekday column
    for (let i = 0; i < firstWeekday; i++) {
        const empty = document.createElement('div');
        empty.className = 'cal-day cal-day-empty';
        grid.appendChild(empty);
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateString = `${_calendarYear}-${String(_calendarMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const hasData    = available.has(dateString);
        const isSelected = dateString === state.date;

        const cell = document.createElement('div');
        cell.textContent = day;
        cell.className   = 'cal-day' +
            (hasData    ? ' cal-day-available'   : ' cal-day-unavailable') +
            (isSelected ? ' cal-day-selected'    : '');

        if (hasData) {
            cell.addEventListener('click', (e) => {
                e.stopPropagation();
                _closeCalendar();
                _onDateSelect(dateString);
            });
        }

        grid.appendChild(cell);
    }
}