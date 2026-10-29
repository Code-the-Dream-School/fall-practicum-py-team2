from dotenv import load_dotenv
import json
from pathlib import Path
import os
from supabase import create_client

# Taked a single JSON file that was previously saved during the extract function and upserts it to superbase. 
# Supabase tables were already made on the platform, with two for raw data (station_information and bike_information). 
# This code runs the load_raw function twice, once for each table.

def load_raw(supabase, file_path, table_name, id_column = "station_id"):
    file_path = Path(file_path)
    with open(file_path, "r") as file:
        data = json.load(file)
        
        # Skip records without an ID: the database can't store a row without its primary key
        valid = [record for record in data if record.get(id_column)]
        skipped = len(data) - len(valid)
        if skipped:
            print(f"Skipped {skipped} record(s) in {file_path.name} missing {id_column}")
        
        if not valid:
            print(f"{file_path.name} is empty, nothing to load into {table_name}")
            return 0
        
        response = (supabase
                    .table(table_name)
                    .upsert(valid, count="exact")
                    .execute())
        print(f"{response.count} rows upserted to {table_name}")
        return response.count

# Main function cycles through existed JSON data and funnels it to the load_raw function.

if __name__ == "__main__":
    # Creates the supabase client
    load_dotenv()
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

    # Passes client and data to the load_raw function
    EXTRACT_DIR = Path(__file__).parent.parent / "extract"
    station_path = EXTRACT_DIR / "station_information.json"
    bike_path = EXTRACT_DIR / "bike_information.json"
    try: 
        rows_loaded = load_raw(supabase.schema("raw"), station_path, "stations_raw")
        rows_loaded += load_raw(supabase.schema("raw"), bike_path, "bike_information", "bike_id")
    except Exception as e:
        raise 