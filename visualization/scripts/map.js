let map;

export const initializeMap = (lat, lng) => {
    if (map) {
        map.remove();
    }

    map = L.map('map', {
        center: [lat, lng],
        zoom: 13,
        zoomSnap: 0.2,
        attributionControl: false,
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(map);
}

export const getMap = () => map;