from dotenv import load_dotenv
import json
import os
from supabase import create_client

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
        print("An error has occured:", e)

if __name__ == "__main__":
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    load_raw(supabase, "../extract/station_information.json", "station_information")
    load_raw(supabase, "../extract/bike_information.json", "bike_information")

