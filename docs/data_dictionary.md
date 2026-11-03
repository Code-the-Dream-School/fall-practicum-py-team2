# Team 2 Data Dictionary: SF Bike Share Analytics Pipeline

This reference document outlines the schemas, data types, constraints, and business logic definitions across our database layers in Supabase.

---

###  1. Enriched Bike Analytics Table Schema (`enriched_bks`)
This table holds the cleansed, transformed, and enriched metrics used to drive frontend map interfaces and answer business queries regarding rider preferences.

| Column Name | Data Type | Constraints | Description / Business Logic Rule | Required? |
| :--- | :---: | :---: | :--- | :---: |
| **`collected_at`** | `TIMESTAMPTZ` | **PRIMARY KEY** | System time recording when the raw dataset snapshot row was captured. | **Yes** |
| **`num_bikes_available`** | `INT4` | — | Total count of operable bicycles ready to rent (classic + e-bikes combined). | Yes |
| **`num_ebikes_available`** | `INT4` | — | Specific count of available electric-assist models ready for customer rental. | No |
| **`num_manual_bikes_available`** | `INT4` | — | Derived calculation: `num_bikes_available - num_ebikes_available`. | No |
| **`capacity`** | `INT4` | **NON-NULLABLE** | Total physical docking points present at the station. | **Yes** |
| **`availability`** | `NUMERIC` | — | Derived calculation: `(num_bikes_available / capacity) * 100`. Rounded to 2 decimals. | Yes |
| **`availability_status`** | `TEXT` | — | Category mapping: `empty` (=0), `low` (0-20), `healthy` (20-90), or `full` (>90). | Yes |
| **`station_id`** | `TEXT` | **PRIMARY KEY** | Mapped unique alphanumeric tracking hash identifying individual stations. | **Yes** |
| **`name`** | `TEXT` | — | Official public-facing text name of the bike share dock station location. | No |
| **`short_name`** | `TEXT` | — | Simplified internal moniker shorthand used by field maintenance operators. | No |
| **`lon`** | `NUMERIC` | **NON-NULLABLE** | Cleaned geospatial longitude location coordinate. Rows missing this are dropped. | **Yes** |
| **`lat`** | `NUMERIC` | **NON-NULLABLE** | Cleaned geospatial latitude location coordinate. Rows missing this are dropped. | **Yes** |
| **`bike_rent_rate`** | `NUMERIC` | — | Derived calculation: `(num_manual_bikes_available / num_bikes_available) * 100`. | No |
| **`ebike_rent_rate`** | `NUMERIC` | — | Derived calculation: `(num_ebikes_available / num_bikes_available) * 100`. | No |

---

###  2. Raw Ingestion Layer Table Schema (`stations_raw`)
This table acts as the initial write-only landing pad where raw snapshot records from the real-time API streams are ingested directly by the extraction engine.

| Column Name | Data Type | Constraints | Description / Context | Required? |
| :--- | :---: | :---: | :--- | :---: |
| **`station_id`** | `TEXT` | **PRIMARY KEY** | Unique identifier string tracking individual stations. | **Yes** |
| **`name`** | `TEXT` | — | Official public name text string. | No |
| **`short_name`** | `TEXT` | — | Maintenance operator code moniker shorthand. | No |
| **`lon`** | `NUMERIC` | **NON-NULLABLE** | Raw geospatial longitude coordinate string. | **Yes** |
| **`lat`** | `NUMERIC` | **NON-NULLABLE** | Raw geospatial latitude coordinate string. | **Yes** |
| **`region_id`** | `TEXT` | — | Sector identifier tracking geographic boundaries. | No |
| **`capacity`** | `NUMERIC` | **NON-NULLABLE** | Total physical docking slots on-site. | **Yes** |
| **`is_installed`** | `BOOL` | — | Boolean tracking if the station is physically setup. | No |
| **`is_renting`** | `BOOL` | — | Boolean tracking if the station is currently renting out cycles. | No |
| **`is_returning`** | `BOOL` | — | Boolean tracking if the station is accepting inbound cycle returns. | No |
| **`last_reported`** | `TIMESTAMPTZ` | **NON-NULLABLE** | Ingestion system check time recording activity. | **Yes** |
| **`collected_at`** | `TIMESTAMPTZ` | **PRIMARY KEY** | Execution timestamp indicating when the log row was written. | **Yes** |
| **`num_bikes_available`** | `NUMERIC` | — | Count of ready-to-rent cycles at the snapshot moment. | No |
| **`num_bikes_disabled`** | `NUMERIC` | — | Count of broken or offline cycles sitting in docks. | No |
| **`num_docks_available`** | `NUMERIC` | — | Count of remaining empty docking spaces. | No |
| **`num_docks_disabled`** | `NUMERIC` | — | Count of damaged or offline docking slots. | No |
| **`num_ebikes_available`** | `NUMERIC` | — | Count of electric-assist models ready on the racks. | No |
| **`num_scooters_available`** | `NUMERIC` | — | Count of available secondary micromobility options. | No |
| **`num_scooters_unavaliable`** | `NUMERIC` | — | Count of broken or locked out secondary micromobility options. | No |

---

###  3. Pipeline Run Diagnostics Table Schema (`logs`)
This operational log table tracks pipeline execution health metrics, run durations, data volumes, and error tracing messages for system auditing.

| Column Name | Data Type | Constraints | Description / Operational Context | Required? |
| :--- | :---: | :---: | :--- | :---: |
| **`run_id`** | `UUID` | **PRIMARY KEY** | Universally Unique Identifier generated automatically for each distinct pipeline run. | **Yes** |
| **`started_at`** | `TIMESTAMPTZ` | — | System clock timestamp recording precisely when the pipeline run script was initiated. | No |
| **`ended_at`** | `TIMESTAMPTZ` | — | System clock timestamp tracking when the execution thread finished processing or crashed. | No |
| **`records_processed`** | `INT4` | — | Total count integer tracking how many data rows were successfully evaluated during this specific run. | No |
| **`status`** | `TEXT` | — | Overall pipeline process tracking outcome labels (e.g., `SUCCESS`, `FAILED`, `IN_PROGRESS`). | No |
| **`message`** | `TEXT` | — | Full text string capturing console system alerts, row summaries, or stack-trace dump messages for error debugging. | No |
