# Docs - Nextbike Data Analysis

NextBike data analysis for your city.
Includes Data gathering, aggregation, cleanup and display.

## 📚️ How to's and Getting Started
[Setup Nextbike analysis for your city](./setup-analysis-for-your-city.md)

## 🏗️ ToDo & Features:

### ⚙️ Processing
- [ ] Remove "trips" that are less than 100m.
- [ ] Removelocations that have "not" changed. (lat,long to small of a difference)

### 🖥️ WEBPAGE
- [X] Add table with trips
    - [X] id, bikeid, start time, end time, distance, trip time
- [ ] Provide downloadbutton for data
- [X] make trip clickable in table, jumps to end time of slider and shows the trip with red, instead of blue color
- [X] make table sortable
- [ ] Add location to columns in table
- [ ] Clicking on trip jumps to map
- [X] Make map "full-screen" 80%. Player, playbutton, time, total trips, current trips and date "inside" the map at the bottom

#### Stations
- [X] Show stations as dots in the map
- [ ] Click on station shows: Name, amount of bikes,
- [ ] Color the Bubble for station on map: red - 0 bikes, yellow up to 10, red starting from 10



- Include docs to setup for given city (where to locate the city id)

