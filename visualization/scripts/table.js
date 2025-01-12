import state from "./state.js";
import { highlightTrip } from "./main.js";

export function populateRouteTable() {
    const tableBody = document.querySelector('#route-table tbody');
    tableBody.innerHTML = '';

    state.tripsData.forEach((trip, index) => {
        const row = document.createElement('tr');
        row.dataset.index = index;

        row.innerHTML = `
            <td>${trip.bike_number}</td>
            <td>${new Date(trip.start_time).toLocaleTimeString()}</td>
            <td>${new Date(trip.end_time).toLocaleTimeString()}</td>
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

    const sortedRows = rows.sort((a, b) => {
        const aData = a.querySelector(`td:nth-child(${column + 1})`).textContent.trim();
        const bData = b.querySelector(`td:nth-child(${column + 1})`).textContent.trim();

        const aValue = isNaN(aData) ? aData : parseFloat(aData);
        const bValue = isNaN(bData) ? bData : parseFloat(bData);

        if (order === 'asc') {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });

    tableBody.innerHTML = '';
    sortedRows.forEach(row => tableBody.appendChild(row));
}

document.querySelectorAll('#route-table th').forEach((header, index) => {
    header.addEventListener('click', () => {
        const currentOrder = header.getAttribute('data-order');
        const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';

        document.querySelectorAll('#route-table th').forEach(otherHeader => {
            otherHeader.setAttribute('data-order', '');
        })


        header.setAttribute('data-order', newOrder);
        sortTable(index, newOrder);
    });
});