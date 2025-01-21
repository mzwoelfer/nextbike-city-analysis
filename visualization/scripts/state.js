const state = {
    city_id: 0,
    city_lat: 0,
    city_lng: 0,
    cities: {},
    tripsData: [],
    activeRoutes: {},
    stationData: [],
    stationMarkers: {},
    markerMap: {},
    isPlaying: false,
    timer: null,
    currentTimeMinutes: 0,
    date: "",
    availableFiles: {},

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
