# Visualize Nextbike data

🚧 WORK IN PROGRESS

## Prerequisites
1. Populated `data/` folder
Each JSON-file contains trips per day.
See the format at the end of this README.

2. Run http-server locally:
```SHELL
cd visualization/

# Start http server
python3 -m http.server 8000
```

3. Visit `localhost:8000` in your browser







## JSON Trip Format
Each json file in `data/` contains a list of bike trips.
Each trip is represented as an object with the following structure:
```JSON
[
    {
        "mode": <STRING> The type of data. "trip",
        "timestamp": <STRING> Start of trip ISO 8601 timestamp. "2024-07-01T15:48:03.220Z",
        "timestampEnd" : <STRING> End of trpi ISO 8601 timestamp. "2024-07-01T16:12:02.645Z",
        "distance" : <NUMBER> total distance in meters. ,
        "duration" : <NUMBER> duration of trip in seconds. ,
        "bikeId" : <NUMBER> unique bike identifier. ,
        "speed" : <NUMBER> average speed in meters per second. ,
        "timeStart" : <NUMBER> start of trip Unix timestamp (in milliseconds). ,
        "timeEnd" : <NUMBER> end of trip Unix timestamp (in milliseconds). ,
        "segments": <ARRAY of ARRAY> Array of GPS coordinates [longitude, latitude] pairs (in decimal degrees).
    }
]
```

Data stolen from [bikesharing-vis](https://github.com/technologiestiftung/bikesharing-vis/blob/master/data/2019-07-02-trails.json)

Example:
```JSON
[
    {
        "mode": "trip",
        "timestamp": "2019-07-01T15:48:03.220Z",
        "timestampEnd": "2019-07-01T16:12:02.645Z",
        "distance": 3043.1,
        "duration": 886.7,
        "bikeId": 13097,
        "speed": 12.3549791361227,
        "timeStart": 1561996083220,
        "timeEnd": 1561997522645,
        "segments": [
            [
                13.394195,
                52.491678
            ],
            [
                13.394461,
                52.491627
            ],
        ]
    }
]
```


## Credits
Incorporation features and concepts from [Bikesharing Vis](https://github.com/technologiestiftung/bikesharing-vis) by [Technologiestiftung Berlin](https://github.com/technologiestiftung)