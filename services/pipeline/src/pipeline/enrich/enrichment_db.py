
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
        .select("station_id,name,lat,lon")
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



# Saving one station's LLM enrichment result to Supabase.
def save_enrichment(supabase, station_id: str, result: dict) -> None:
    """
    Preparing a station enrichment record.
    Saving the record to the Gold Layer.
    Avoiding duplicate records using station_id.
    """
    # Preparing the enrichment record.
    record = {
        "station_id": station_id,
        "station_zone_profile": result["station_zone_profile"],
        "commuter_density_impact": result["commuter_density_impact"],
        "enrichment_summary": result["enrichment_summary"],
        "model_name": result["model_name"],
        "prompt_version": result["prompt_version"],
    }

    # Saving the record using station_id as the unique key.
    (
        supabase.schema("gold")
        .table("station_enrichments")
        .upsert(record, on_conflict="station_id")
        .execute()
    )



# Recording a station's enrichment failure in Supabase.
def save_enrichment_error(supabase, station_id: str, error_message: str) -> None:
    """
    Preparing an error record for a failed station.
    Saving the error in the logs schema.
    Recording the station ID and error message.
    """
    # Preparing the error record.
    record = {
        "station_id": station_id,
        "error_message": error_message,
    }

    # Saving the error in the database.
    (
        supabase.schema("logs")
        .table("enrichment_errors")
        .insert(record)
        .execute()
    )
