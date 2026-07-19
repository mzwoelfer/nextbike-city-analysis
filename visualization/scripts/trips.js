import { getMap } from './map.js';
import state from './state.js';
import { minutesSinceMidnight } from './utils.js';

/**
 * Draw all currently active trips on the map.
 * @returns {void}
 */
export function drawTripsOnMap() {
    const map = getMap();
    const { tripsData, currentTimeMinutes, activeRoutes, city_timezone } = state;

    if (!tripsData || tripsData.length === 0) {
        return;
    }

    tripsData.forEach((trip, index) => {
        const { tripStartMinute, tripEndMinute } = getTripMinuteWindow(trip, city_timezone);

        if (isTripActiveAtMinute(currentTimeMinutes, tripStartMinute, tripEndMinute)) {
            const segmentCount = getVisibleSegmentCount(
                trip.coordinates.length,
                currentTimeMinutes,
                tripStartMinute,
                tripEndMinute,
            );
            const activeRouteState = activeRoutes[index];

            if (activeRouteState && activeRouteState.lastSegmentCount === segmentCount) {
                return;
            }

            const visiblePathCoordinates = buildVisibleTripPathCoordinates(trip, segmentCount);

            if (visiblePathCoordinates.length > 1) {
                removeRouteLayerFromMap(map, activeRouteState);

                activeRoutes[index] = {
                    layer: buildFadingRouteLayer(visiblePathCoordinates).addTo(map),
                    lastSegmentCount: segmentCount,
                };
            }
        } else {
            if (activeRoutes[index]) {
                removeRouteLayerFromMap(map, activeRoutes[index]);
                delete activeRoutes[index];
            }
        }
    });
}

/**
 * Highlight one trip on the map and jump playback to its start minute.
 * @param {number} index - Trip index in state.tripsData.
 * @returns {void}
 */
export function highlightTripOnMap(index) {
    const map = getMap();
    const trip = state.tripsData[index];
    if (!trip) {
        return;
    }

    const { tripStartMinute } = getTripMinuteWindow(trip, state.city_timezone);
    state.currentTimeMinutes = tripStartMinute;

    Object.values(state.activeRoutes).forEach((routeState) => {
        removeRouteLayerFromMap(map, routeState);
    });
    state.activeRoutes = {};

    const fullTripPathCoordinates = trip.coordinates.map(([lon, lat]) => [lat, lon]);
    const selectedRoute = L.polyline(fullTripPathCoordinates, {
        color: 'var(--accent)',
        weight: 4,
    }).addTo(map);

    if (fullTripPathCoordinates.length > 0) {
        map.panTo(fullTripPathCoordinates[0]);
    }

    state.activeRoutes[index] = {
        layer: selectedRoute,
        lastSegmentCount: trip.coordinates.length,
    };
}

/**
 * Resolve the trip minute window for a trip.
 * @param {Object} trip - Trip data object.
 * @param {string} cityTimezone - Timezone used for fallback conversion.
 * @returns {{ tripStartMinute: number, tripEndMinute: number }} Trip minute range.
 */
function getTripMinuteWindow(trip, cityTimezone) {
    return {
        tripStartMinute: trip.start_minute_city
            ?? minutesSinceMidnight(new Date(trip.start_time), cityTimezone),
        tripEndMinute: trip.end_minute_city
            ?? minutesSinceMidnight(new Date(trip.end_time), cityTimezone),
    };
}

/**
 * Check whether a trip is active at the selected minute.
 * @param {number} currentMinute - Current playback minute.
 * @param {number} tripStartMinute - Trip start minute.
 * @param {number} tripEndMinute - Trip end minute.
 * @returns {boolean} True when the trip is active.
 */
function isTripActiveAtMinute(currentMinute, tripStartMinute, tripEndMinute) {
    return currentMinute >= tripStartMinute && currentMinute <= tripEndMinute;
}

/**
 * Calculate how many route segments should be visible for the current playback minute.
 * @param {number} coordinateCount - Number of trip coordinates.
 * @param {number} currentMinute - Current playback minute.
 * @param {number} tripStartMinute - Trip start minute.
 * @param {number} tripEndMinute - Trip end minute.
 * @returns {number} Visible segment count.
 */
function getVisibleSegmentCount(coordinateCount, currentMinute, tripStartMinute, tripEndMinute) {
    const elapsedFraction = (currentMinute - tripStartMinute) / (tripEndMinute - tripStartMinute || 1);
    return Math.floor(elapsedFraction * coordinateCount);
}

/**
 * Build the portion of a trip path that should currently be rendered.
 * @param {Object} trip - Trip data object.
 * @param {number} segmentCount - Number of visible segments.
 * @returns {Array<Array<number>>} Leaflet path coordinates.
 */
function buildVisibleTripPathCoordinates(trip, segmentCount) {
    return trip.coordinates
        .slice(0, Math.max(segmentCount, 0))
        .map(([lon, lat]) => [lat, lon]);
}

/**
 * Remove one rendered route layer from the map.
 * @param {Object} map - Leaflet map instance.
 * @param {Object} routeState - Stored route state.
 * @returns {void}
 */
function removeRouteLayerFromMap(map, routeState) {
    if (!routeState) {
        return;
    }

    const routeLayer = routeState.layer ?? routeState;
    map.removeLayer(routeLayer);
}

/**
 * Build a layered route that fades from start to end.
 * @param {Array<Array<number>>} pathCoordinates - Leaflet path coordinates.
 * @returns {Object} Leaflet layer group.
 */
function buildFadingRouteLayer(pathCoordinates) {
    const map = getMap();
    const fadingLayers = [];
    const totalSegments = pathCoordinates.length - 1;

    for (let index = 0; index < totalSegments; index++) {
        const start = pathCoordinates[index];
        const end = pathCoordinates[index + 1];
        const opacity = (index + 1) / totalSegments;

        const segmentLayer = L.polyline([start, end], {
            color: 'var(--accent)',
            weight: 3,
            opacity,
        });

        segmentLayer.addTo(map);
        fadingLayers.push(segmentLayer);
    }

    return L.layerGroup(fadingLayers);
}