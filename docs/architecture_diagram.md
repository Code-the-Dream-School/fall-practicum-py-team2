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

    %% Data Pipeline Steps (Matched exactly to Jira Requirements)
    API["1. Input Configuration<br>(SF Bay Wheels Master Catalog gbfs.json)"]:::blue
    
    EXTRACT["2. Python extract.py Engine<br>(Retrieves JSON Payload via HTTP)"]:::teal
    
    TRANSFORM["3. Data Transformation Layer<br>(Filters SF Region '3' & Norms to Pacific Time)"]:::teal
    
    RAW["4. Raw Storage Layer<br>(Bronze Level Staging for Snapshots)"]:::green

    LOAD["5. Local Storage Tracks<br>(station_information.csv & bike_information.csv)"]:::green
    
    DB[("6. Supabase Database<br>(Gold Analytical Storage Tables)")]:::green
    
    ORCH["7. Orchestrated Flow<br>(Prefect Flow Scheduler Loops)"]:::teal

    DASH["8. React Map Dashboard<br>(Responsive Maps & Depletion Charts)"]:::green

    AWS["9. Future Sprint Cloud Migration<br>(AWS Pipeline Scaling Staging)"]:::indigo

    %% Flow Connections
    API --> EXTRACT
    EXTRACT --> TRANSFORM
    TRANSFORM --> RAW
    RAW --> LOAD
    LOAD --> DB
    DB --> DASH
    DASH --> AWS
    ORCH -.-> EXTRACT
```

---

### 2. Core Pipeline Components Explained
* **Input Configuration (Blue):** Live master configurations from the SF Bay Wheels GBFS auto-discovery catalog endpoint (`gbfs.json`), capturing dynamic system snapshot links [6.0].
* **Teal Engines:** Our Python data execution layer querying endpoints via HTTP requests, filtering strictly for San Francisco coordinates (`region_id == '3'`), and normalizing execution timestamps to Pacific Time (`America/Los_Angeles`) [6.0].
* **Raw Storage & Local Storage Tracks (Green):** Our pipeline export architecture managing a raw data storage snapshot layer before saving processed datasets locally to clean tracking files (`station_information.csv` and `bike_information.csv`) [6.0].
* **Supabase & UI (Green):** Loading structured records into target database columns to power our frontend React map dashboard tracking metrics like `utilization_rate` [6.0].
* **Orchestrated Flow (Teal):** Our automated scheduling loop controlled by Prefect to handle steady, repetitive snapshot capture cycles.
* **Indigo Cloud Plan:** Our high-level architecture blueprint plan to transition our local automation engines into highly scalable cloud computing triggers later in the project lifecycle.
