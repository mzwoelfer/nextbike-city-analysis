let map;

export const initializeMap = (lat, lng) => {
    if (map) {
        map.remove();
    }

    map = L.map('map', {
        center: [lat, lng],
        zoom: 13,
        zoomSnap: 0.2,
        attributionControl: true,
    });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
    }).addTo(map);
}

export const getMap = () => map;