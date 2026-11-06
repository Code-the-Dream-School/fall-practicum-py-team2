

from pipeline.enrich.llm_enrichment import (
    enrich_station,
    enrich_stations,
    get_pending_stations,
    MODEL_NAME,
    PROMPT_VERSION,
)

from unittest.mock import MagicMock
from pipeline.enrich.enrichment_db import get_gold_stations, get_enriched_station_ids
from pipeline.enrich.llm_enrichment import run_enrichment

# Testing enrichment with an empty station list.
def test_enrich_stations_empty_input():
    # Tracking unexpected LLM calls.
    calls = []

    # Simulating an LLM without making an API request.
    def fake_llm(prompt):
        calls.append(prompt)
        return "{}"

    # Processing an empty station list.
    result = enrich_stations([], fake_llm)

    # Checking for empty enrichment results and errors.
    assert result["enriched"] == {}
    assert result["errors"] == {}

    # Confirming that no LLM calls are being made.
    assert calls == []


# Testing duplicate stations without repeating LLM calls.
def test_enrich_stations_duplicate_ids():
    # Tracking the number of LLM calls.
    calls = []

    # Simulating a successful LLM response.
    def fake_llm(prompt):
        calls.append(prompt)
        return (
            '{"station_zone_profile": "transit_hub", '
            '"commuter_density_impact": "high", '
            '"enrichment_summary": "Near public transportation."}'
        )

    # Preparing two records with the same station ID.
    stations = [
        {"station_id": "S001", "name": "Broadway at Kearny St"},
        {"station_id": "S001", "name": "Broadway at Kearny St"},
    ]

    # Enriching the station records.
    result = enrich_stations(stations, fake_llm)

    # Confirming that only one station is being enriched.
    assert len(result["enriched"]) == 1
    assert "S001" in result["enriched"]

    # Confirming that the LLM is being called only once.
    assert len(calls) == 1

    # Confirming that no errors are being recorded.
    assert result["errors"] == {}


# Testing LLM failures without stopping other stations.
def test_enrich_stations_handles_errors():

    # Simulating an LLM response and a failure.
    def fake_llm(prompt):
        if "Station Two" in prompt:
            raise RuntimeError("LLM request failed")

        return (
            '{"station_zone_profile": "transit_hub", '
            '"commuter_density_impact": "high", '
            '"enrichment_summary": "Near public transportation."}'
        )

    # Preparing three stations for enrichment.
    stations = [
        {"station_id": "S001", "name": "Station One"},
        {"station_id": "S002", "name": "Station Two"},
        {"station_id": "S003", "name": "Station Three"},
    ]

    # Processing the stations using the fake LLM.
    result = enrich_stations(stations, fake_llm)

    # Checking that successful stations are being recorded.
    assert "S001" in result["enriched"]
    assert "S003" in result["enriched"]

    # Checking that the failed station is not being enriched.
    assert "S002" not in result["enriched"]

    # Checking that the failure is being recorded.
    assert result["errors"]["S002"] == "LLM request failed"


# Testing the selection of stations waiting for enrichment.
def test_get_pending_stations():
    # Preparing stations from the Gold Layer.
    stations = [
        {"station_id": "S001", "name": "Station One"},
        {"station_id": "S002", "name": "Station Two"},
        {"station_id": "S003", "name": "Station Three"},
        {"station_id": "S002", "name": "Station Two"},
    ]

    # Identifying stations already enriched.
    enriched_ids = {"S001", "S003"}

    # Selecting stations that still need enrichment.
    pending = get_pending_stations(stations, enriched_ids)

    # Checking that only the new station is being selected.
    assert len(pending) == 1
    assert pending[0]["station_id"] == "S002"


# Testing model and prompt version tracking.
def test_enrich_station_metadata():
    # Simulating a successful LLM response.
    def fake_llm(prompt):
        return (
            '{"station_zone_profile": "transit_hub", '
            '"commuter_density_impact": "high", '
            '"enrichment_summary": "Near public transportation."}'
        )

    # Enriching a station using the fake LLM.
    result = enrich_station("Station One", fake_llm)

    # Checking the recorded model and prompt version.
    assert result["model_name"] == MODEL_NAME
    assert result["prompt_version"] == PROMPT_VERSION

    # Checking the expected prompt version.
    assert result["prompt_version"] == "v1"


# Testing the reading of Gold Layer stations.
def test_get_gold_stations():
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Preparing two fake station records.
    stations = [
        {"station_id": "S001", "name": "Station One"},
        {"station_id": "S002", "name": "Station Two"},
    ]

    # Simulating the database response.
    fake_db.schema().table().select().execute().data = stations

    # Reading the stations using the fake database.
    result = get_gold_stations(fake_db)

    # Checking the returned station records.
    assert result == stations


# Testing the reading of previously enriched station IDs.
def test_get_enriched_station_ids():
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Preparing previously enriched station records.
    records = [
        {"station_id": "S001"},
        {"station_id": "S002"},
        {"station_id": "S001"},
    ]

    # Simulating the database response.
    fake_db.schema().table().select().execute().data = records

    # Reading the previously enriched station IDs.
    result = get_enriched_station_ids(fake_db, "station_enrichments")

    # Checking that only unique station IDs are returned.
    assert result == {"S001", "S002"}

    # Checking the database table being requested.
    fake_db.schema().table.assert_called_with("station_enrichments")



# Testing the incremental LLM enrichment workflow.
def test_run_enrichment():
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Preparing Gold Layer station records.
    stations = [
        {"station_id": "S001", "name": "Station One"},
        {"station_id": "S002", "name": "Station Two"},
        {"station_id": "S003", "name": "Station Three"},
    ]

    # Preparing previously enriched station IDs.
    existing = [
        {"station_id": "S001"},
        {"station_id": "S003"},
    ]

    # Simulating different database responses.
    # fake_db.schema().table().select().execute().data = stations
    # fake_db.schema().table().select("station_id").execute().data = existing

    
    # Simulating separate responses for Gold and enrichment tables.
    def fake_table(table_name):
        # Creating a separate fake table for each query.
        table = MagicMock()

        # Returning Gold Layer stations.
        if table_name == "enriched_bks":
            table.select().execute().data = stations

        # Returning previously enriched station IDs.
        elif table_name == "station_enrichments":
            table.select().execute().data = existing

        return table

    # Selecting the correct fake table by name.
    fake_db.schema.return_value.table.side_effect = fake_table


    # Tracking LLM calls.
    calls = []

    # Simulating a successful LLM response.
    def fake_llm(prompt):
        calls.append(prompt)
        return (
            '{"station_zone_profile": "transit_hub", '
            '"commuter_density_impact": "high", '
            '"enrichment_summary": "Near public transportation."}'
        )

    # Running the enrichment workflow.
    result = run_enrichment(fake_db, fake_llm, "station_enrichments")

    # Checking that only Station Two is enriched.
    assert list(result["enriched"]) == ["S002"]

    # Checking that the LLM is called only once.
    assert len(calls) == 1
    assert "Station Two" in calls[0]

    # Checking that no errors are recorded.
    assert result["errors"] == {}
