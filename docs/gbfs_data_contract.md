# Data Contract — Team 2 (Bike Share GBFS)
---
### 1. Function Signatures
```python
def extract(feed_url: str) -> dict:
    """
    Queries the central GBFS auto-discovery master catalog URL 
    to dynamically extract child dictionary data.
    """
    pass

def to_csv(df, file_path: str) -> None:
    """
    Saves processed DataFrames locally to CSV tracking files 
    prior to analytical database loading.
    """
    pass
```
---
### 2. Input & Quality Rules
* **Target Feeds:** `station_information.json` (Static layout) & `station_status.json` (Live metrics).

* **Target Master Feed:** `https://gbfs.lyft.com/gbfs/2.3/bay/gbfs.json` (Auto-discovers structural sub-feeds).
* **Region Filtering:** Pipeline strictly isolates records where `region_id == "3"` (San Francisco).
* **Geospatial Bounding:** Free-floating bikes are dynamically bounded using the minimum and maximum coordinates of active stations to filter out stray locations.

* **Data Dropping:** If a record lacks a valid `station_id` or GPS coordinates, drop it from processing.
* **Missing Counts:** If bike or dock numbers are missing, default them to `0`.

---

### 3. Data Schemas

#### Raw Schema (Bronze Layer)
The extraction module returns raw dictionary data structures, which the pipeline workflow then processes and appends locally into CSV tracking files prior to analytical database loading:

* **File Track 1:** `station_information.csv`
* **Columns:** `station_id`, `name`, `short_name`, `lon`, `lat`, `region_id`, `is_charging`, `address`, `num_bikes_available`, `num_bikes_disabled`, `num_docks_available`, `num_docks_disabled`, `is_installed`, `is_renting`, `is_returning`, `last_reported`

* **File Track 2:** `bike_information.csv`
* **Columns:** `bike_id`, `lon`, `lat`, `is_reserved`, `is_disabled`, `current_range_meters`, `vehicle_type_id`, `form_factor`, `propulsion_type`, `max_range_meters`

---

#### Gold Schema (Analytics Layer)
* **Granularity:** One flat row per asset per timestamp execution.
* **Database Target:** Structured tables optimized for React map dashboard rendering.
* **Example Station Record:**
```json
{
  "timestamp": "2026-10-09T13:11:00Z",
  "station_id": "c4c4484d-0e18-44dd",
  "station_name": "Williams Ave at 3rd St",
  "latitude": 37.72927,
  "longitude": -122.39289,
  "bikes_available": 2,
  "docks_available": 16,
  "capacity": 18,
  "utilization_rate": 0.11
}
```
