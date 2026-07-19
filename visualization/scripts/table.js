import state from "./state.js";
import { highlightTrip } from "./main.js";
import { formatTimeInTimezone } from "./utils.js";

export function populateRouteTable() {
    const tableBody = document.querySelector('#route-table tbody');
    tableBody.innerHTML = '';

    state.tripsData.forEach((trip, index) => {
        const row = document.createElement('tr');
        row.dataset.index = index;

        row.innerHTML = `
            <td>${trip.bike_number}</td>
            <td>${formatTimeInTimezone(trip.start_time, state.city_timezone)}</td>
            <td>${formatTimeInTimezone(trip.end_time, state.city_timezone)}</td>
            <td>${trip.distance.toFixed(2)}</td>
            <td>${Math.floor(trip.duration / 60)}</td>
        `;

        row.addEventListener('click', () => highlightTrip(index));
        tableBody.appendChild(row);
    });
}

export function highlightTableRow(index) {
    document.querySelectorAll('#route-table tbody tr').forEach((row) => row.classList.remove('active'));
    document.querySelector(`[data-index='${index}']`).classList.add('active');
}

export function sortTable(column, order) {
    const tableBody = document.querySelector('#route-table tbody');
    const rows = Array.from(tableBody.querySelectorAll('tr'));

    const sortedRows = rows.sort((rowA, rowB) => {
        const columnValueA = extractSortValue(rowA, column);
        const columnValueB = extractSortValue(rowB, column);

        return order === 'asc'
            ? (columnValueA > columnValueB ? 1 : -1)
            : (columnValueA < columnValueB ? 1 : -1);
    });

    tableBody.innerHTML = '';
    sortedRows.forEach(row => tableBody.appendChild(row));
}

/**
 * Extract the sortable value from one table row's column cell.
 * @param {HTMLElement} row - Table row element.
 * @param {number} column - Zero-based column index.
 * @returns {string|number} Cell text, parsed to a number when numeric.
 */
function extractSortValue(row, column) {
    const cell = row.querySelector(`td:nth-child(${column + 1})`);
    const cellText = cell.textContent;
    const trimmedText = cellText.trim();

    return isNaN(trimmedText) ? trimmedText : parseFloat(trimmedText);
}

document.querySelectorAll('#route-table th').forEach((header, index) => {
    header.addEventListener('click', () => {
        const currentOrder = header.getAttribute('data-order');
        const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';

        document.querySelectorAll('#route-table th').forEach(otherHeader => {
            otherHeader.setAttribute('data-order', '');
        });

        header.setAttribute('data-order', newOrder);
        sortTable(index, newOrder);
    });
});