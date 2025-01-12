import { getMap } from './map.js';
import state from './state.js';

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