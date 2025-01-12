import { getMap } from './map.js';
import state from './state.js';
import { minutesSinceMidnight } from './utils.js';


export function createFadingPolyline(pathCoordinates) {
    const map = getMap();
    // polylines for fading effect
    const fadingLayers = [];
    const totalSegments = pathCoordinates.length - 1;

    for (let i = 0; i < totalSegments; i++) {
        const start = pathCoordinates[i];
        const end = pathCoordinates[i + 1];
        const opacity = (i + 1) / totalSegments;

        const polyline = L.polyline([start, end], {
            color: '#91785D',
            weight: 3,
            opacity: opacity,
        });

        polyline.addTo(map);
        fadingLayers.push(polyline);
    }

    return L.layerGroup(fadingLayers);
}

export function drawTrips() {
    const map = getMap();
    const { tripsData, currentTimeMinutes, activeRoutes } = state;

    if (!tripsData || tripsData.length === 0) return;

    const currentTime = new Date(tripsData[0].start_time);
    currentTime.setHours(0, 0, 0, 0);
    currentTime.setMinutes(currentTimeMinutes);

    tripsData.forEach((trip, index) => {
        const tripStart = new Date(trip.start_time);
        const tripEnd = new Date(trip.end_time);

        if (currentTime >= tripStart && currentTime <= tripEnd) {
            const pathCoordinates = trip.segments
                .filter(([_, __, timestamp]) => new Date(timestamp) <= currentTime)
                .map(([lat, lon]) => [lat, lon]);

            if (pathCoordinates.length > 1) {
                // Remove existing previous routes
                if (activeRoutes[index]) {
                    map.removeLayer(activeRoutes[index]);
                }

                activeRoutes[index] = createFadingPolyline(pathCoordinates).addTo(map);
            }
        } else {
            if (activeRoutes[index]) {
                map.removeLayer(activeRoutes[index]);
                delete activeRoutes[index];
            }
        }
    });
}


export function highlightTripOnMap(index) {
    const map = getMap();
    const trip = state.tripsData[index];
    if (!trip) return;
    const tripStartTime = new Date(trip.start_time);
    state.currentTimeMinutes = minutesSinceMidnight(tripStartTime);

    Object.values(state.activeRoutes).forEach((route) => map.removeLayer(route));
    state.activeRoutes = {};

    const pathCoordinates = trip.segments.map(([lat, lon]) => [lat, lon]);
    const selectedRoute = L.polyline(pathCoordinates, { color: 'red', weight: 4 }).addTo(map);

    if (pathCoordinates.length > 0) {
        map.panTo(pathCoordinates[0]);
    }

    state.activeRoutes[index] = selectedRoute;
}