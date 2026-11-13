import os
from pathlib import Path
from dotenv import load_dotenv
from prefect import flow, task
from supabase import create_client

# Import your team's individual scripts
from src.pipeline.extract.extract import run_extract
from src.pipeline.load.load_raw import load_raw
from src.pipeline.transform.transform_gold import transform_and_load_to_gold

# 1. Extract Task  (3 retries just in case of unexpected network fails)
@task(retries=3, retry_delay_seconds=10)
def extract_task():
    print("Starting extraction...")
    run_extract()
    print("Extraction complete. JSON files saved locally.")

# 2. Load Task (Database gets 1 retry in case of a connection fail)
@task(retries=1, retry_delay_seconds=5)
def load_raw_task():
    print("Starting raw data load...")
    load_dotenv()
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    
    # Pathing based on where extract.py dumps the files
    BASE_DIR = Path.cwd()
    station_path = BASE_DIR / "station_information.json"
    bike_path = BASE_DIR / "bike_information.json"
    
    stations_loaded = load_raw(supabase.schema("raw"), station_path, "stations_raw", "station_id")
    bikes_loaded = load_raw(supabase.schema("raw"), bike_path, "bike_information", "bike_id")
    
    return stations_loaded + bikes_loaded

# 3. Transform Task
@task
def transform_task():
    print("Starting gold layer transformation...")
    gold_df = transform_and_load_to_gold()
    return len(gold_df)

# 4. The Master Control Flow
@flow(name="Bike-Share-ETL-Pipeline", log_prints=True)
def run_bike_pipeline(run_mode: str = "production"):
    print(f"Pipeline run started in {run_mode} mode.")
    print("START: Pipeline run started.")
    
    # Run Extract
    extract_task()
    
    # Run Load
    rows_loaded = load_raw_task()
    print(f"LOAD: Loaded {rows_loaded} total raw rows into Supabase.")
    
    # Run Transform
    rows_transformed = transform_task()
    print(f"TRANSFORM: Transformed {rows_transformed} rows in the Gold layer.")
    
    print("FINSIHED: Pipeline run completed successfully!")
    
    # Return or record a structured result (KAN-26 requirement)
    return {
        "status": "success",
        "rows_extracted": "Saved to JSON",
        "rows_loaded": rows_loaded,
        "rows_transformed": rows_transformed
    }

if __name__ == "__main__":
    run_bike_pipeline()