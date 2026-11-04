
import json
from pathlib import Path


# Function 1: Loading the LLM prompt and inserting the station name.
def load_prompt(station_name: str) -> str:
    """
    Reading the prompt from a text file.
    Replacing the placeholder with the station name.
    Returning the completed prompt.
    """

    # Finding the prompt file.
    prompt_path = Path(__file__).parent / "prompts" / "station_profiler.txt"

    # Opening the file and reading the instructions.
    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt = file.read()

    # Replacing the placeholder with the station name.
    return prompt.replace("{station_name}", station_name)


# Function 2: Validating the LLM response and handling invalid values.
def validate_llm_response(response_text: str) -> dict:
    """
    Converting the JSON response into a Python dictionary.
    Checking the values against the KAN-23 contract.
    Applying fallback values when needed.
    """

    # Defining default values for invalid responses.
    defaults = {
        "station_zone_profile": "commercial_district",
        "commuter_density_impact": "moderate",
        "enrichment_summary": (
            "Fallback: Location profile generated "
            "due to malformed LLM response string."
        ),
    }

    # Converting JSON text into a Python dictionary.
    try:
        result = json.loads(response_text)

    # Handling malformed JSON.
    except (json.JSONDecodeError, TypeError):
        return defaults.copy()

    # Checking whether the response is a dictionary.
    if not isinstance(result, dict):
        return defaults.copy()

    # Defining the allowed station categories.
    allowed_zones = {
        "transit_hub",
        "commercial_district",
        "residential_neighborhood",
        "recreational_park",
    }

    # Defining the allowed commuter density values.
    allowed_density = {"high", "moderate", "low"}

    # Getting and checking the station category.
    zone = result.get("station_zone_profile")

    if not isinstance(zone, str) or not zone.strip():
        zone = defaults["station_zone_profile"]
    elif zone not in allowed_zones:
        zone = "recreational_park"

    # Getting and checking the commuter density.
    density = result.get("commuter_density_impact")

    if density not in allowed_density:
        density = defaults["commuter_density_impact"]

    # Getting and checking the enrichment summary.
    summary = result.get("enrichment_summary")

    if not isinstance(summary, str) or not summary.strip():
        summary = defaults["enrichment_summary"]

    # Returning the validated fields and limiting the summary length.
    return {
        "station_zone_profile": zone,
        "commuter_density_impact": density,
        "enrichment_summary": summary[:150],
    }


# Function 3: Enriching one bike station using an LLM.
def enrich_station(station_name: str, llm_call) -> dict:
    """
    Preparing the prompt for a bike station.
    Calling the provided LLM function.
    Validating and returning the enrichment results.
    """

    # Loading the prompt with the station name.
    prompt = load_prompt(station_name)

    # Sending the prompt to the LLM.
    response_text = llm_call(prompt)

    # Validating and returning the LLM response.
    return validate_llm_response(response_text)


# Function 4: Enriching multiple bike stations and handling individual failures.
def enrich_stations(stations: list, llm_call) -> dict:
    """
    Processing multiple bike stations using the LLM.
    Skipping duplicate station IDs and missing station names.
    Recording errors without stopping the remaining stations.
    """

    # Creating a dictionary for successful enrichment results.
    enriched = {}

    # Creating a dictionary for stations that failed.
    errors = {}

    # Tracking station IDs already processed in this batch.
    seen_ids = set()

    # Processing each station from the input list.
    for station in stations:
        station_id = station.get("station_id")
        station_name = station.get("name")

        # Skipping stations with missing IDs or invalid names.
        if (
            not station_id
            or not isinstance(station_name, str)
            or not station_name.strip()
        ):
            continue

        # Skipping repeated station IDs within the same batch.
        if station_id in seen_ids:
            continue

        seen_ids.add(station_id)

        # Calling the LLM and recording the enrichment result.
        try:
            result = enrich_station(station_name, llm_call)
            enriched[station_id] = result

        # Recording errors while continuing with the next station.
        except Exception as error:
            errors[station_id] = str(error)

    # Returning successful results and recorded errors.
    return {
        "enriched": enriched,
        "errors": errors,
    }



# Function 5: Selecting stations that still need LLM enrichment.
def get_pending_stations(stations: list, enriched_ids: set) -> list:
    """
    Checking which stations have already been enriched.
    Selecting only new stations for LLM processing.
    Skipping duplicate station IDs and invalid names.
    """

    # Creating a list for stations waiting for enrichment.
    pending = []

    # Tracking station IDs already selected in this batch.
    seen_ids = set()

    # Checking each station from the input list.
    for station in stations:
        station_id = station.get("station_id")
        station_name = station.get("name")

        # Skipping stations with missing IDs or invalid names.
        if (
            not station_id
            or not isinstance(station_name, str)
            or not station_name.strip()
        ):
            continue

        # Skipping stations already enriched or already selected.
        if station_id in enriched_ids or station_id in seen_ids:
            continue

        # Recording the station ID to prevent duplicates.
        seen_ids.add(station_id)

        # Adding the station to the pending list.
        pending.append(station)

    # Returning only stations that still need enrichment.
    return pending
