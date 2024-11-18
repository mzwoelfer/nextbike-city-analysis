const map = L.map('map').setView([50.5851475, 8.6643273], 8);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap contributors'
}).addTo(map);


async function loadTrips(trip_file){
    try{
        const response = await fetch(trip_file);
        if (!response.ok){
            throw new Error(`Error fetching Nextbike Trip data! Status: ${response.status}`);
        }

        const data = await response.json();
        data.forEach(trip => {
            if (trip.segments.length > 0) {
                const route = trip.segments;
                L.polyline(route, { color: 'blue', weight: 3}).addTo(map);
                map.fitBounds(route);
            }
        });
    } catch (error) {
        console.error("Error loading trip data:", error)
    }
}

loadTrips('data/06-11-2024-trips.json')
