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

    EXTRACT["2. Python extract.py Engine<br>(Retrieves JSON Payload via HTTP)"]:::teal
    
    CSV["3. Data Transformation Layer<br>(Filters SF Region '3' & Norms to Pacific Time)"]:::teal
    
    LOAD["4. Local Storage Tracks<br>(station_information.csv & bike_information.csv)"]:::green

    
    DB[("5. Supabase Database<br>(Gold Analytical Storage Tables)")]:::green
    
    DASH["6. React Map Dashboard<br>(Responsive Maps & Depletion Charts)"]:::green

    AWS["7. Future Sprint Cloud Migration<br>(AWS Pipeline Scaling Staging)"]:::indigo


    %% Flow Connections
    API --> EXTRACT
    EXTRACT --> CSV
    CSV --> LOAD
    LOAD --> DB
    DB --> DASH
    AWS -.-> EXTRACT
```

---

### 2. Core Pipeline Components Explained
** **Blue (Source):** Live feeds from the SF Bay Wheels GBFS auto-discovery catalog endpoint (`gbfs.json`), capturing dynamic system snapshots [6.0].
* **Teal (Engine):** Our Python data execution layer querying endpoints via HTTP requests, filtering strictly for San Francisco coordinates (`region_id == '3'`), and normalizing execution timestamps to Pacific Time (`America/Los_Angeles`) [6.0].
* **Green (Storage & UI):** Our pipeline export architecture saving processed data locally to clean tracking files (`station_information.csv` and `bike_information.csv`) before loading structured records into Supabase to power our frontend React map dashboard [6.0].
* **Indigo (Cloud Plan):** Our high-level architecture blueprint plan to transition our local automation engines into highly scalable cloud computing triggers later in the project lifecycle.
