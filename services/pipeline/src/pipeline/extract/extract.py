import requests
import pandas as pd

# Function to grab data
def extract(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()['data']

BASE_URL = "https://gbfs.lyft.com/gbfs/2.3/bay/gbfs.json" # The outermost url looking at gbfs.json. All other data/urls are accessible from here.
REGION_ID = "3"

# Get dictionary of URLS
main_feed = extract(BASE_URL)['en']['feeds']
feed_urls = {feed['name'] : feed ['url'] for feed in main_feed}

# Collect and organize station information
info = pd.DataFrame(extract(feed_urls['station_information'])['stations'])
status = pd.DataFrame(extract(feed_urls['station_status'])['stations'])
stations = info.merge(status, on="station_id", how="left")
stations = stations[stations["region_id"] == REGION_ID]
stations = stations.drop(columns=['rental_uris', 'vehicle_types_available'])
stations['last_reported'] = pd.to_datetime(stations['last_reported'], unit='s', utc=True).dt.tz_convert('America/Los_Angeles')
stations.to_csv('./station_information.csv', index=False)

# Collect and organize bike information
free_bike = pd.DataFrame(extract(feed_urls['free_bike_status'])['bikes'])
bike_type = pd.DataFrame(extract(feed_urls['vehicle_types'])['vehicle_types'])
bikes = free_bike.merge(bike_type, on="vehicle_type_id", how="left")
in_sf = (bikes['lat'].between(stations['lat'].min(), stations['lat'].max())
         & bikes['lon'].between(stations['lon'].min(), stations['lon'].max()))
bikes = bikes[in_sf]
bikes = bikes[in_sf].drop(columns=['rental_uris'])
bikes.to_csv('./bike_information.csv', index=False)