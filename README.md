# NJTransit Scraper
#### v4.1 2021 Dec 4
Anthony Townsend <atownsend@cornell.edu>

### dependencies

- ```pip3 install mysqlclient``` is the only way to get mysql connection to work


## function

Fetches list of active routes from NJTransit Clever Devices API http requests, then cycles through and fetches current vehicle positions for all buses operating on these routes. This avoids the poor performance of trying to grab the entire system feed from the MTA BusTime SIRI API. Dumps full API response (for later reprocessing to extract additional data) to compressed individual files and most of the vehicle status fields to mysql table (the upcoming stop data is omitted from the database dump for now). Fully dockerized, runs on scheduler 1x per minute. Data storage requirments ~ 1-2 Gb/day (guesstimate).


## installation 

### (docker)

1. clone the repo

    `git clone https://github.com/anthonymobile/nycbuswatcher.git`
    
2. obtain a MapBox API key and put it in .env (quotes not needed apparently)
    - MapBox

    ```txt
    MAPBOX_API_KEY = pk.ey42424fasjhfasfajskjrwer242jk424242
    ```
    
3. build and run the images

    ```
    cd nycbuswatcher
    docker-compose up -d --build
    ```

### (manual)

1. clone the repo

    `git clone https://github.com/Cornell-Tech-Urban-Tech-Hub/njbuswatcher.git`
    
2. obtain a Mapbox API key from http://bustime.mta.info/wiki/Developers/Index/ and put it in .env

    `echo 'MAPBOX_API_KEY = pk.ey42424fasjhfasfajskjrwer242jk424242' > .env`
    
3. create the database (mysql only, 5.7 recommended)
    ```sql
    CREATE DATABASE buses_nj;
    USE buses_nj;
    CREATE USER 'njbuswatcher'@'localhost' IDENTIFIED BY 'njtransit';
    GRANT ALL PRIVILEGES ON * . * TO 'njbuswatcher'@'localhost';
    FLUSH PRIVILEGES;
 
    ```
3. run
    ```python
    python grabber.py # development: run once and quit
    python grabber.py -p # production: runs in infinite loop at set interval using scheduler (hardcoded for now)
    ```

# usage 

## 1. localhost production mode

if you just want to test out the grabber, you can run `export PYTHON_ENV=development; python grabber.py -l` and it will run once, dump the responses to a pile of files, and quit after throwing a database connection error. (or not, if you did step 3 in "manual" above). if you have a mysql database running it will operate in production mode locally until stopped.

## 2. docker stack

### grabber

1. get a shell on the container and run another instance of the script, it should run with the same environment as the docker entrypoint and will spit out any errors that process is having without having to hunt around through log files
    ```
    docker exec -it njbuswatcher_grabber_1 /bin/bash
    python buswatcher.py
    ```
 

### mysql database

talking to a database inside a docker container is a little weird

1. *connect to mysql inside a container* to start a mysql client inside a mysql docker container

    ```
    docker exec -it njbuswatcher_db_1 mysql -uroot -p buses_nj
    [root password=bustime]
    ```
    
2. quick diagnostic query for how many records per day

    ```sql
   SELECT DATE(timestamp), COUNT(*) FROM buses GROUP BY DATE(timestamp);
    ```
    
3. query # of records by date/hour/minute

    ```sql
     SELECT DATE(timestamp), date_format(timestamp,'%Y-%m-%d %H-%i'), COUNT(*) \
     FROM buses GROUP BY DATE(timestamp), date_format(timestamp,'%Y-%m-%d %H-%i');
    ```

## 3. API

The v2 API returns a selected set of fields for all positions during a time interval specific using ISO 8601 format for a single route at a time. e.g.

Required arguments: `rt, start, end`
Output is in geojson.

```json
http://nj.buswatcher.org/api/v2/nj/buses?rt=119&start=2021-03-28T00:00:00+00:00&end=2021-04-28T01:00:00+00:00
```

### live positions

```json
http://nj.buswatcher.org/api/v2/nj/buses/now
```