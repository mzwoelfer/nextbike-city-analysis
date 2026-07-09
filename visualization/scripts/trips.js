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
            color: 'var(--accent)',
            weight: 3,
            opacity: opacity,
        });

        polyline.addTo(map);
        fadingLayers.push(polyline);
    }

    return L.layerGroup(fadingLayers);
}

function removeActiveRoute(map, routeState) {
    if (!routeState) return;
    const layer = routeState.layer ?? routeState;
    map.removeLayer(layer);
}

export function drawTrips() {
    const map = getMap();
    const { tripsData, currentTimeMinutes, activeRoutes, city_timezone } = state;

    if (!tripsData || tripsData.length === 0) return;

    tripsData.forEach((trip, index) => {
        const tripStartMinutes = trip.start_minute_city ?? minutesSinceMidnight(new Date(trip.start_time), city_timezone);
        const tripEndMinutes = trip.end_minute_city ?? minutesSinceMidnight(new Date(trip.end_time), city_timezone);

        if (currentTimeMinutes >= tripStartMinutes && currentTimeMinutes <= tripEndMinutes) {
            const elapsed = (currentTimeMinutes - tripStartMinutes) / (tripEndMinutes - tripStartMinutes || 1);
            const segmentCount = Math.floor(elapsed * trip.coordinates.length); 
            const activeRouteState = activeRoutes[index];

            if (activeRouteState && activeRouteState.lastSegmentCount === segmentCount) {
                return;
            }

            const pathCoordinates = trip.coordinates.slice(0, Math.max(segmentCount, 0)).map(([lon, lat]) => [lat, lon]);

            if (pathCoordinates.length > 1) {
                removeActiveRoute(map, activeRouteState);

                activeRoutes[index] = {
                    layer: createFadingPolyline(pathCoordinates).addTo(map),
                    lastSegmentCount: segmentCount,
                };
            }
        } else {
            if (activeRoutes[index]) {
                removeActiveRoute(map, activeRoutes[index]);
                delete activeRoutes[index];
            }
        }
    });
}


export function highlightTripOnMap(index) {
    const map = getMap();
    const trip = state.tripsData[index];
    if (!trip) return;
    state.currentTimeMinutes = trip.start_minute_city ?? minutesSinceMidnight(new Date(trip.start_time), state.city_timezone);

    Object.values(state.activeRoutes).forEach((routeState) => removeActiveRoute(map, routeState));
    state.activeRoutes = {};

    const pathCoordinates = trip.coordinates.map(([lon, lat]) => [lat, lon]);
    const selectedRoute = L.polyline(pathCoordinates, { color: 'var(--accent)', weight: 4 }).addTo(map);

    if (pathCoordinates.length > 0) {
        map.panTo(pathCoordinates[0]);
    }

    state.activeRoutes[index] = {
        layer: selectedRoute,
        lastSegmentCount: trip.coordinates.length,
    };
}