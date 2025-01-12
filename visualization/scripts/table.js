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