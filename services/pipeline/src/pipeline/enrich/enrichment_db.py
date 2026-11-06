
import os
from dotenv import load_dotenv
from supabase import create_client


# Creating a Supabase client using environment credentials.
def get_supabase_client():
    """
    Loading database credentials from the environment.
    Checking that the required credentials are available.
    Creating and returning a Supabase client.
    """
    # Loading environment variables from the .env file.
    load_dotenv()

    # Reading the Supabase credentials.
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    # Checking for missing credentials.
    if not supabase_url or not supabase_key:
        raise ValueError("Missing Supabase credentials")

    # Creating and returning the database client.
    return create_client(supabase_url, supabase_key)


# Reading bike station records from the Gold Layer.
def get_gold_stations(supabase) -> list:
    """
    Reading station records from the Gold Layer.
    Selecting station IDs and station names.
    Returning the records as a list.
    """
    # Querying the Gold Layer table.
    response = (
        supabase.schema("gold")
        .table("enriched_bks")
        .select("station_id,name")
        .execute()
    )

    # Returning the station records.
    return response.data


# Reading station IDs that already have enrichment results.
def get_enriched_station_ids(supabase, table_name: str) -> set:
    """
    Reading previously enriched station IDs.
    Converting the IDs into a set.
    Returning the IDs for skipping repeated enrichment.
    """
    # Reading station IDs from the selected Gold Layer table.
    response = (
        supabase.schema("gold")
        .table(table_name)
        .select("station_id")
        .execute()
    )

    # Collecting the station IDs into a set.
    return {
        row["station_id"]
        for row in response.data
        if row.get("station_id")
    }
