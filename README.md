# bike-sharing

🚧 WORK IN PROGRESS

- Data collection: `src/`
- 


## Data Collection
src/

### Overview
- create a database
- setup the script on a server
- run script automated with a cron job

### Prerequisites

- Python 3.12
- Python libraries: [requirementxt.txt](/requirements.txt)

install packages:
    pip install -r requirements.txt

### Scripts
**SQL Script [create_bike_and_stations_db.sql](/src/create_bike_and_stations_db.sql) to create the database scheme**

Create a database where the data queried in the script is being stored.

**Script [query_nextbike.py](/src/query_nextbike.py) is used to query provider API data**

API requests to receive current bike and station locations from Nextbike in Gießen and store them in a postgres database.


**Config File**
Add [config.py](/src/config.py) file to `src/` with database credentials.

## Run script automized
Set up a cron job that runs the script in regular intervalls.
E.g. this setup
- run the *query_nextbike.py* script every minute

**CRON JOBS**
        * * * * * python3 [PATH TO FOLDER]/src/query_nextbike.py

### Query other cities or providers
To query other providers [this documentation](https://github.com/ubahnverleih/WoBike/) is a good source of information.

## Data Analysis
src/analysis

1. Add your postgres credentials into `config.py`
2. Calculate the trips: `python3 calculate_trips.py`
3. Show trips: `python3 plot_trips.py`

- giessen_minimal_route.png - visualized Nextbike routes in city
- config.py - COnfig to connect to postgres and pull data
- calculate_trips.py - calculates trips from data and output trips.csv
- plot_trips.py - plots the trips from trips.csv to an image
- trips.csv - Holds the trips data with start and end location and timestamp

