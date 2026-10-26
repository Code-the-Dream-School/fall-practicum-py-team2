from dotenv import load_dotenv
import json
import os
from supabase import create_client

# Taked a single JSON file that was previously saved during the extract function and upserts it to superbase. 
# Supabase tables were already made on the platform, with two for raw data (station_information and bike_information). 
# This code runs the load_raw function twice, once for each table.

def load_raw(supabase, file_name, table_name):
    try:
        with open(file_name, "r") as file:
            data = json.load(file)
            response = (supabase
                        .table(table_name)
                        .upsert(data, count="exact")
                        .execute())
            if response.count > 0:
                print(f"{response.count} rows upserted to {table_name}")
            else:
                print("No new rows")
    except Exception as e:
        e.raise_for_status

# Main function cycles through existed JSON data and funnels it to the load_raw function.

if __name__ == "__main__":
    # Creates the supabase client
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    # Passes client and data to the load_raw function
    load_raw(supabase, "../extract/station_information.json", "station_information")
    load_raw(supabase, "../extract/bike_information.json", "bike_information")