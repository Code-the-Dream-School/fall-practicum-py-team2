# Supabase tables
## SQL Request
CREATE TABLE IF NOT EXISTS stations_raw (
  station_id TEXT NOT NULL, 
  name TEXT, 
  short_name TEXT, 
  lon numeric NOT NULL, 
  lat numeric NOT NULL, 
  region_id TEXT, 
  capacity INTEGER NOT NULL,
  is_charging BOOLEAN, 
  address TEXT, 
  num_bikes_available INTEGER, 
  num_bikes_disabled INTEGER, 
  num_docks_available INTEGER, 
  num_docks_disabled INTEGER, 
  is_installed BOOLEAN, 
  is_renting BOOLEAN, 
  is_returning BOOLEAN, 
  last_reported TIMESTAMPTZ NOT NULL,
  collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  num_ebikes_available INTEGER,
  num_scooters_available INTEGER,
  num_scooters_unavailable INTEGER,
  PRIMARY KEY (station_id, collected_at)
);


CREATE TABLE IF NOT EXISTS enriched_bks (
  collected_at TIMESTAMPTZ NOT NULL,
  num_bikes_available INTEGER,
  num_ebikes_available INTEGER,
  num_manual_bikes_available INTEGER,
  availability NUMERIC,
  availability_status TEXT,
  capacity INTEGER NOT NULL
  station_id TEXT NOT NULL, 
  name TEXT, 
  short_name TEXT, 
  lon numeric NOT NULL, 
  lat numeric NOT NULL,
  bike_rent_rate NUMERIC,
  ebike_rent_rate NUMERIC,
  PRIMARY KEY (station_id, collected_at)
);

CREATE TABLE IF NOT EXISTS logs (
  run_id UUID PRIMARY KEY,
  started_at TIMESTAMPTZ NOT NULL,
  ended_at TIMESTAMPTZ,
  records_processed INTEGER,
  status TEXT NOT NULL,
  message TEXT NOT NULL
);
The script is supposed to be run in the SQL editor of Supabase dashboard.

## stations_raw
Table contains raw data from station_information.json
Column	Data type	Constraints	Description
station_id	TEXT	NOT NULL, part of Primary key	- Station identifier
name	TEXT	—	Station name
short_name	TEXT	—	Short station name
lon	NUMERIC	NOT NULL -	Longitude
lat	NUMERIC	NOT NULL -	Latitude
region_id	TEXT	—	GBFS region identifier
capacity	INTEGER	NOT NULL	-  Station capacity
is_charging	BOOLEAN	—	Whether the station supports charging
address	TEXT	—	Station address
num_bikes_available	INTEGER	—	Number of available bikes
num_bikes_disabled	INTEGER	—	Number of disabled bikes
num_docks_available	INTEGER	—	Number of available docks
num_docks_disabled	INTEGER	—	Number of disabled docks
is_installed	BOOLEAN	—	Whether the station currently on the street
is_renting	BOOLEAN	—	Whether the station currently renting vehicles
is_returning	BOOLEAN	—	Whether the station accepting vehicle returns
last_reported	TIMESTAMPTZ	NOT NULL -	The last time this station reported its status to the operator's backend.
collected_at	TIMESTAMPTZ	NOT NULL, DEFAULT now(), part of Primary key -	Time the record was collected
num_ebikes_available	INTEGER	—	Number of available e-bikes
num_scooters_available	INTEGER	—	Number of available scooters
num_scooters_unavailable	INTEGER	—	Number of unavailable scooters
Primary key: (station_id, collected_at)

## enriched_bks
The table contains cleaned and enriched data
Column	Data type	Constraints	Description
collected_at 	TIMESTAMPTZ	NOT NULL, part of PK -	Time the record was collected (from raw data)
num_bikes_available	INTEGER	—	Total number of available bikes (total number of e-bikes and manual bikes available from raw data)
num_ebikes_available	INTEGER	—	Number of available e-bikes (from raw data)
num_manual_bikes_available	INTEGER	—	Available manual bikes (The difference between total number of bikes and number of e-bikes)
capacity INTEGER NOT NULL	-  Station capacity
availability	NUMERIC	—	Availability rate,  num_bikes_available / capacity * 100%
availability_status	TEXT	—	Availability status (low, medium, high depending on availability)
station_id	TEXT	NOT NULL, part of PK -	Station identifier
name	TEXT	—	Station name
short_name	TEXT	—	Short station name
lon	NUMERIC	NOT NULL	Longitude
lat	NUMERIC	NOT NULL	Latitude
bike_rent_rate	NUMERIC	—	Manual-bike rental rate, num_manual_bikes_available / num_bikes_available * 100%
ebike_rent_rate	NUMERIC	—	E-bike rental rate, num_ebikes_available / num_bikes_available * 100%
Primary key: (station_id, collected_at)

## logs
The table contains pipeline logs
Column	Data type	Constraints	Description
run_id	UUID	PRIMARY KEY	Unique pipeline run identifier
started_at	TIMESTAMPTZ	NOT NULL	Pipeline run start time
ended_at	TIMESTAMPTZ	Nullable	Pipeline run completion time
records_processed	INTEGER	Nullable	Number of records processed
status	TEXT	NOT NULL	Run status, e.g. success or failed
message	TEXT	NOT NULL	Run summary or error message
Primary key: run_id