# 🗺️ Team 2 Refined Architecture Diagram (SF Bike Share GBFS)

This flowchart outlines how our San Francisco Bike Share data moves from the public API into our local file tracks, analytical databases, and downstream user dashboard metrics [INDEX].

---

### 1. Visual Infrastructure Flowchart

```mermaid
graph TD
    %% Styling Configuration
    classDef blue fill:#0284c7,stroke:#0369a1,stroke-width:2px,color:#fff;
    classDef teal fill:#0d9488,stroke:#0f766e,stroke-width:2px,color:#fff;
    classDef green fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef indigo fill:#4f46e5,stroke:#4338ca,stroke-width:2px,color:#fff;

    %% Data Pipeline Steps (Matched exactly to Data Contract)
    API["1. Lyft Master Feed<br>(https://gbfs.lyft.com/gbfs/2.3/bay/gbfs.json)"]:::blue

    EXTRACT["2. def extract(url)<br>(Filters for SF Region ID '3')"]:::teal
    
    CSV["3. def to_csv(df, file_path)<br>(station_information.csv & bike_information.csv)"]:::green
    
    DB[("4. Supabase Database<br>(Gold Analytics Layer Schema)")]:::green
    
    DASH["5. Frontend Dashboard<br>(Live Map & utilization_rate)"]:::green

    AWS["6. Future AWS Cloud Staging<br>(EventBridge + Lambda Container)"]:::indigo

    %% Flow Connections
    API --> EXTRACT
    EXTRACT --> CSV
    CSV --> DB
    DB --> DASH
    AWS -.-> EXTRACT
```

---

### 2. Core Pipeline Components Explained
* **Blue (Source):** The dynamic, live public Lyft master feed (`https://gbfs.lyft.com/gbfs/2.3/bay/gbfs.json`) providing auto-discovery access to station and status structures.
* **Teal (Engine):** Our Python execution layer running `extract(url)` to filter data strictly down to San Francisco (`region_id == "3"`) and apply geospatial boundary truncations [INDEX].
* **Green (Storage & UI):** Our local storage handlers calling `to_csv()` for station and bike logs, updating our indexed time-series tables in Supabase, and mapping fields like `utilization_rate` directly onto the interactive client dashboard map.
* **Indigo (Cloud Plan):** Our architecture blueprint to host our decoupled data collection script inside a serverless AWS Lambda cron workflow container later [INDEX].
