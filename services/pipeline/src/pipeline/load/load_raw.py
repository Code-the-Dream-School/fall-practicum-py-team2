from dotenv import load_dotenv
import json
from Path import pathlib
import os
from supabase import create_client

# Taked a single JSON file that was previously saved during the extract function and upserts it to superbase. 
# Supabase tables were already made on the platform, with two for raw data (station_information and bike_information). 
# This code runs the load_raw function twice, once for each table.

def load_raw(supabase, file_path, table_name):
    if file_path.exists():
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                response = (supabase
                            .table(table_name)
                            .upsert(data, count="exact")
                            .execute())
                if response.count > 0:
                    print(f"{response.count} rows upserted to {table_name}")
                elif response.count==0:
                    print("No new rows")
                else:
                    response.raise_for_status
        except Exception as e:
            print("An error has occured:", e)
    else:
        print("No such file exists")

# Main function cycles through existed JSON data and funnels it to the load_raw function.

if __name__ == "__main__":
    # Creates the supabase client
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    # Passes client and data to the load_raw function
    station_path = Path("../extract/station_information.json")
    bike_path = Path( "../extract/bike_information.json")
    load_raw(supabase, station_path, "stations_raw")
    load_raw(supabase, bike_path, "bike_information")

