# Bikeshare Team 2 Product Summary 

## Purpose and Dataset Choice
This document explains the data pipeline our team is building for the Lyft Bike project (PKA Bay Wheels). We selected the SF Bay Wheels GBFS (v2.3) dataset because the San Francisco network provides a dense dual-fleet system of both electric and classic bikes, making it ideal for tracking urban mobility patterns. Our product answers a specific problem: **how does bike availability fluctuate at individual stations during peak commute hours, and do riders show a measurable preference (rapid depletion) for e-bikes over regular manual bikes?**

## The Data Our Product Needs
Because we are still refining the exact metrics for our dashboard, our pipeline will initially extract the complete raw data payload. 

Our product requires live feeds from the SF Bay Wheels GBFS auto-discovery catalog (`gbfs.json`), specifically focusing on region `3` (San Francisco):
* **Station Data:** Fields from `station_information` (station ID, name, latitude, longitude, region ID) combined with real-time metrics from `station_status` (available bikes, available docks, and status timestamps).
* **Vehicle & Fleet Data:** Fields from `free_bike_status` and `vehicle_types` to capture dockless bikes, map vehicle type IDs, and differentiate electric bikes from classic pedal bikes.

## The ETL Pipeline Stages
Our pipeline automates the data preparation process through three standard stages:
* **Extract:** The pipeline queries the Lyft GBFS base feed (`https://gbfs.lyft.com/gbfs/2.3/bay/gbfs.json`) to discover endpoints. It retrieves JSON payloads for stations, live station statuses, free bikes, and vehicle types via HTTP requests.
* **Transform:** The pipeline parses raw payloads into structured tables, filters for San Francisco stations and coordinates, normalizes timestamps to Pacific Time (`America/Los_Angeles`), and joins station and vehicle datasets to calculate inventory metrics and e-bike ratios.
* **Load:** The pipeline exports intermediate snapshot datasets (`station_information.csv`, `bike_information.csv`) and loads cleaned records into the database for persistent tracking and analytical queries.

## Dashboard Integration
Our React map dashboard reads from the prepared database and aggregated datasets. Because the pipeline handles API extractions, coordinate filtering, time-zone conversions, and metric calculations in the background, the dashboard can reliably present responsive geographic maps, station-level inventory trackers, and peak-hour e-bike versus classic bike comparison charts without calling external APIs on page load.