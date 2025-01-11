const state = {
    city_id: 467,
    city_lat: 0,
    city_lng: 0,
    cities: {
        "Gießen": 467,
        "Marburg": 438
    },
    tripsData: [],
    activeRoutes: {},
    stationData: [],
    stationMarkers: {},
    markerMap: {},
    isPlaying: false,
    timer: null,
    currentTimeMinutes: 0,
    date: "2024-12-20",

    nextDay() {
        const currentDate = new Date(this.date);
        currentDate.setDate(currentDate.getDate() + 1);
        this.date = currentDate.toISOString().split('T')[0];
    },
    previousDay() {
        const currentDate = new Date(this.date);
        currentDate.setDate(currentDate.getDate() - 1);
        this.date = currentDate.toISOString().split('T')[0];
    },
};

export default state;
