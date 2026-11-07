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

def transform_and_load_to_gold() -> pd.DataFrame:
    """
    Downloads raw time-series logs, standardizes types, applies type-safe missing
    value handling, computes rolling averages, and derives structural analytics fields.
    """
    pass
```
---
## 2. Input & Quality Rules

* **Target Feeds:** `station_information` (Static layout structural data) & `station_status` (Live occupancy telemetry metrics).
* **Target Master Feed:** `https://lyft.com` (Auto-discovers regional tracking endpoints).
* **Region Filtering:** Pipeline strictly isolates records where `region_id == "3"` (San Francisco area).
* **Geospatial Bounding:** Free-floating bikes are dynamically bounded using the coordinates of active stations to filter out outlier logs.
* **Data Dropping:** If a row lacks a valid `station_id`, `lat`, or `lon`, it is immediately dropped from the processing matrix.
* **Missing Value Fallbacks:** Completely handles missing entries type-safely. Numeric fields default to `0.0`, while text fields map to empty strings (`""`) to protect database serialization constraints.

---
## 3. Data Schemas

### Raw Schema (Staging Layer)
The extraction engine ingests real-time snapshot layers directly from the source endpoints into our write-only Supabase tables:

* **Table Target 1: `stations_raw`**
  * Columns: `station_id` (PK), `collected_at` (PK), `name`, `short_name`, `lat`, `lon`, `capacity`, `num_bikes_available`, `num_ebikes_available`, `num_docks_available`, `is_installed`, `is_renting`, `is_returning`, `last_reported`
* **Table Target 2: `bike_information`**
  * Columns: `bike_id`, `lon`, `lat`, `is_reserved`, `is_disabled`, `current_range_meters`, `vehicle_type_id`, `propulsion_type`

### Gold Schema (Analytics Layer)
* **Granularity:** One flat row per active station asset per timestamp execution slice.
* **Database Target Table:** `enriched_bks`
* **Example Station Record Output:**

```json
{
  "collected_at": "2026-10-30 17:49:00",
  "station_id": "c4c44b4d-de18-44dd-8ef2-efbc80ad1234",
  "name": "Broadway at Kearny St",
  "short_name": "SF-M21",
  "lat": 37.79854,
  "lon": -122.40695,
  "capacity": 28,
  "num_bikes_available": 14,
  "num_ebikes_available": 10,
  "num_manual_bikes_available": 4,
  "availability": 50.00,
  "rolling_avg_score": 48.50,
  "availability_status": "healthy",
  "bike_rent_rate": 28.57,
  "ebike_rent_rate": 71.43
}
```

#### Status Classification Reference Logic:
* **`empty`** ➔ `availability == 0.00`
* **`low`** ➔ `0.00 < availability <= 20.00`
* **`healthy`** ➔ `20.00 < availability < 90.00`
* **`full`** ➔ `availability >= 90.00`
