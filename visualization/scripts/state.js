const state = {
    city_id: 0,
    city_lat: 0,
    city_lng: 0,
    city_timezone: "UTC",
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
    useApi: true,

    nextDay() {
        const [year, month, day] = this.date.split('-').map(Number);
        const currentDate = new Date(Date.UTC(year, month - 1, day));
        currentDate.setUTCDate(currentDate.getUTCDate() + 1);
        this.date = currentDate.toISOString().split('T')[0];
    },
    previousDay() {
        const [year, month, day] = this.date.split('-').map(Number);
        const currentDate = new Date(Date.UTC(year, month - 1, day));
        currentDate.setUTCDate(currentDate.getUTCDate() - 1);
        this.date = currentDate.toISOString().split('T')[0];
    },
};

export default state;
