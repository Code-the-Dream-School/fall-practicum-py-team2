# Data Contract — Team 2 (Bike Share GBFS)
---
### 1. Function Signatures
```python
def extract(feed_url: str) -> dict:
    """Fetches raw JSON payload from the GBFS API endpoint."""
    pass

def load_raw(raw_payload: dict, feed_type: str, db_client) -> bool:
    """Appends unparsed JSON wrapped with extraction metadata to Supabase."""
    pass

def transform(raw_info: dict, raw_status: dict) -> list[dict]:
    """Flattens, cleans, and combines raw records into Gold analytics rows."""
    pass
```
---
### 2. Input & Quality Rules
* **Target Feeds:** `station_information.json` (Static layout) & `station_status.json` (Live metrics).

* **Isolation Rule:** All functions take plain data primitives and read secrets from environment variables. Connection client handles (`db_client`) are an exception to allow database storage interactions.

* **Data Dropping:** If a record lacks a valid `station_id` or GPS coordinates, drop it from processing.
* **Missing Counts:** If bike or dock numbers are missing, default them to `0`.

---
#### 🗄️ Raw Schema (Bronze Layer)
* **Database Columns:** `id` (UUID), `extracted_at` (Timestamp), `feed_type` (Text), `feed_url` (Text), `raw_json` (JSONB)
* **Example Payload:**
```json
{
  "extracted_at": "2026-10-04T22:00:00Z",
  "feed_type": "station_status",
  "feed_url": "https://baywheels.com",
  "raw_json": {
    "data": {
      "stations": [{ "station_id": "st_82", "num_bikes_available": 10, "num_docks_available": 5 }]
    }
  }
}
```

#### Gold Schema (Analytics Layer)
* **Granularity:** One flat row per station per timestamp extraction.
* **Database Columns:** `timestamp`, `station_id`, `station_name`, `latitude`, `longitude`, `bikes_available`, `docks_available`, `capacity`, `utilization_rate`
* **Example Payload:**
```json
{
  "timestamp": "2026-10-04T22:00:00Z",
  "station_id": "st_82",
  "station_name": "Broadway & 14th St",
  "latitude": 37.8044,
  "longitude": -122.2712,
  "bikes_available": 10,
  "docks_available": 5,
  "capacity": 15,
  "utilization_rate": 0.67
}
```
