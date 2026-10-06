import state from "./state.js";
import { formatTimeInTimezone } from "./utils.js";

export function populateRouteTable(onHighlightTrip) {
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

        row.addEventListener('click', () => onHighlightTrip(index));
        tableBody.appendChild(row);
    });
}

export function populateUniqueRoutesTable() {
    const tableBody = document.querySelector('#unique-routes-table tbody');
    const routes = new Map();

    state.tripsData.forEach((trip) => {
        if (trip.route_id == null) return;

        const routeKey = String(trip.route_id);
        const route = routes.get(routeKey);
        if (route) {
            route.tripCount += 1;
            return;
        }

        routes.set(routeKey, {
            routeId: trip.route_id,
            distance: Number.isFinite(Number(trip.distance)) ? Number(trip.distance) : null,
            start: trip.coordinates?.[0],
            end: trip.coordinates?.at(-1),
            tripCount: 1,
        });
    });

    tableBody.replaceChildren();
    const sortedRoutes = [...routes.values()].sort((routeA, routeB) => Number(routeA.routeId) - Number(routeB.routeId));

    if (sortedRoutes.length === 0) {
        const row = tableBody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 5;
        cell.textContent = 'No routed trips for this date.';
        return;
    }

    sortedRoutes.forEach((route) => {
        const row = tableBody.insertRow();
        const values = [
            route.routeId,
            route.distance == null ? 'N/A' : route.distance.toFixed(2),
            formatRouteEndpoint(route.start),
            formatRouteEndpoint(route.end),
            route.tripCount,
        ];

        values.forEach((value) => {
            row.insertCell().textContent = String(value);
        });
    });
}

function formatRouteEndpoint(coordinates) {
    if (!Array.isArray(coordinates) || coordinates.length < 2) return 'N/A';
    const [longitude, latitude] = coordinates.map(Number);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return 'N/A';
    return `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
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