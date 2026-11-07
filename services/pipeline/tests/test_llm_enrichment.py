
import pytest
from pipeline.enrich.llm_enrichment import (
    enrich_station,
    enrich_stations,
    get_pending_stations,
    MODEL_NAME,
    PROMPT_VERSION,
    run_enrichment,
    call_openai,
    run_openai_enrichment,
)

from unittest.mock import MagicMock, patch

from pipeline.enrich.enrichment_db import (
get_gold_stations,
get_enriched_station_ids,
save_enrichment,
save_enrichment_error
)


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
        # Creating reusable fake database tables.
    gold_table = MagicMock()
    enrichment_table = MagicMock()

    # Preparing fake responses.
    gold_table.select().execute().data = stations
    enrichment_table.select().execute().data = existing

    # Returning the correct fake table.
    def fake_table(table_name):
        if table_name == "enriched_bks":
            return gold_table

        if table_name == "station_enrichments":
            return enrichment_table

        raise ValueError("Unexpected table name")
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
    
    # Checking that the enriched station is being saved.
    saved_table = fake_db.schema.return_value.table(
        "station_enrichments"
    )

    # Confirming that one database save is being requested.
    saved_table.upsert.assert_called_once_with(
        {
            "station_id": "S002",
            **result["enriched"]["S002"],
        },
        on_conflict="station_id",
    )

    # Confirming that the database save is being executed.
    saved_table.upsert.return_value.execute.assert_called_once()




# Testing the saving of enrichment results.
def test_save_enrichment():
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Preparing a sample enrichment result.
    result = {
        "station_zone_profile": "transit_hub",
        "commuter_density_impact": "high",
        "enrichment_summary": "Near public transportation.",
        "model_name": "test-model",
        "prompt_version": "v1",
    }

    # Saving the result using the fake database.
    save_enrichment(fake_db, "S001", result)

    # Preparing the expected database record.
    expected_record = {
        "station_id": "S001",
        **result,
    }

    # Checking the selected database schema and table.
    fake_db.schema.assert_called_once_with("gold")
    fake_db.schema.return_value.table.assert_called_once_with(
        "station_enrichments"
    )

    # Checking the saved record and duplicate protection.
    fake_db.schema.return_value.table.return_value.upsert.assert_called_once_with(
        expected_record,
        on_conflict="station_id",
    )


# Testing the handling of database saving failures.
def test_save_enrichment_database_error():
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Simulating a database failure during saving.
    fake_db.schema().table().upsert().execute.side_effect = RuntimeError(
        "Database connection failed"
    )

    # Preparing a sample enrichment result.
    result = {
        "station_zone_profile": "transit_hub",
        "commuter_density_impact": "high",
        "enrichment_summary": "Near public transportation.",
        "model_name": "test-model",
        "prompt_version": "v1",
    }

    # Checking that the database error is being raised.
    with pytest.raises(RuntimeError, match="Database connection failed"):
        save_enrichment(fake_db, "S001", result)



# Testing continued processing when one database save fails.
def test_run_enrichment_handles_save_failure():
    
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Preparing Gold Layer stations.
    stations = [
        {"station_id": "S001", "name": "Station One"},
        {"station_id": "S002", "name": "Station Two"},
        {"station_id": "S003", "name": "Station Three"},
    ]

    # Creating reusable fake database tables.
    gold_table = MagicMock()
    enrichment_table = MagicMock()

    # Simulating Gold records and no previous enrichments.
    gold_table.select().execute().data = stations
    enrichment_table.select().execute().data = []

    # Selecting the correct fake table.
    def fake_table(table_name):
        if table_name == "enriched_bks":
            return gold_table
        if table_name == "station_enrichments":
            return enrichment_table
        raise ValueError("Unexpected table name")

    fake_db.schema.return_value.table.side_effect = fake_table

    # Simulating a failed database save for S002.
    def fake_upsert(record, on_conflict):
        if record["station_id"] == "S002":
            raise RuntimeError("Database save failed")
        return MagicMock()

    enrichment_table.upsert.side_effect = fake_upsert

    # Simulating a successful LLM response.
    def fake_llm(prompt):
        return (
            '{"station_zone_profile": "transit_hub", '
            '"commuter_density_impact": "high", '
            '"enrichment_summary": "Near public transportation."}'
        )

    # Running the enrichment workflow.
    #result = run_enrichment(fake_db, fake_llm, "station_enrichments")
    
    # Mocking error logging while running the enrichment workflow.
    with patch(
        "pipeline.enrich.enrichment_db.save_enrichment_error"
    ) as mock_log:
        result = run_enrichment(
            fake_db, fake_llm, "station_enrichments"
        )

        # Checking that the database saving failure is logged.
        mock_log.assert_called_once_with(
            fake_db, "S002", "Database save failed"
        )


    # Checking the failed station's error.
    assert result["errors"]["S002"] == "Database save failed"

    # Checking that all three saves are attempted.
    assert enrichment_table.upsert.call_count == 3

    # Checking that S003 is attempted after S002 fails.
    assert enrichment_table.upsert.call_args_list[-1].args[0]["station_id"] == "S003"
    
    # Checking that successfully saved stations remain in the results.
    assert "S001" in result["enriched"]
    assert "S003" in result["enriched"]

    # Checking that the failed station is removed from successful results.
    assert "S002" not in result["enriched"]



# Testing the saving of enrichment errors.
def test_save_enrichment_error():
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Recording a station enrichment failure.
    save_enrichment_error(
        fake_db,
        "S002",
        "LLM request failed"
    )

    # Checking the selected database schema.
    fake_db.schema.assert_called_once_with("logs")

    # Checking the selected error table.
    fake_db.schema.return_value.table.assert_called_once_with(
        "enrichment_errors"
    )

    # Checking the error record being inserted.
    fake_db.schema.return_value.table.return_value.insert.assert_called_once_with(
        {
            "station_id": "S002",
            "error_message": "LLM request failed",
        }
    )

    # Checking that the database request is being executed.
    fake_db.schema.return_value.table.return_value.insert.return_value.execute.assert_called_once()

# Testing the logging of failed LLM enrichment requests.
def test_run_enrichment_logs_llm_error():
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Preparing one station.
    stations = [
        {"station_id": "S001", "name": "Station One"}
    ]

    # Creating fake database tables.
    gold_table = MagicMock()
    enrichment_table = MagicMock()

    # Returning one Gold station and no previous enrichments.
    gold_table.select().execute().data = stations
    enrichment_table.select().execute().data = []

    # Selecting the correct fake table.
    def fake_table(table_name):
        if table_name == "enriched_bks":
            return gold_table
        if table_name == "station_enrichments":
            return enrichment_table
        raise ValueError("Unexpected table name")

    fake_db.schema.return_value.table.side_effect = fake_table

    # Simulating an LLM request failure.
    def fake_llm(prompt):
        raise RuntimeError("LLM request failed")

    # Mocking the error logging function.
    with patch(
        "pipeline.enrich.enrichment_db.save_enrichment_error"
    ) as mock_log:
        # Running the enrichment workflow.
        result = run_enrichment(
            fake_db, fake_llm, "station_enrichments"
        )

        # Checking that the error is recorded.
        assert result["errors"]["S001"] == "LLM request failed"

        # Checking that the logging function is called correctly.
        mock_log.assert_called_once_with(
            fake_db, "S001", "LLM request failed"
        )




# Testing continued execution when error logging fails.
def test_run_enrichment_handles_logging_failure():
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Preparing one Gold Layer station.
    stations = [{"station_id": "S001", "name": "Station One"}]

    # Creating fake database tables.
    gold_table = MagicMock()
    enrichment_table = MagicMock()

    # Returning one station and no existing enrichments.
    gold_table.select().execute().data = stations
    enrichment_table.select().execute().data = []

    # Selecting the correct fake table.
    def fake_table(table_name):
        if table_name == "enriched_bks":
            return gold_table
        if table_name == "station_enrichments":
            return enrichment_table
        raise ValueError("Unexpected table name")

    fake_db.schema.return_value.table.side_effect = fake_table

    # Simulating an LLM failure.
    def fake_llm(prompt):
        raise RuntimeError("LLM request failed")

    # Simulating a failure while saving the error log.
    with patch(
        "pipeline.enrich.enrichment_db.save_enrichment_error",
        side_effect=RuntimeError("Logging database unavailable"),
    ):
        # Running the workflow without stopping.
        result = run_enrichment(
            fake_db, fake_llm, "station_enrichments"
        )

    # Checking that the original error is still returned.
    assert result["errors"]["S001"] == "LLM request failed"

    # Checking that no station is reported as successfully enriched.
    assert result["enriched"] == {}



# Testing the OpenAI request without calling the real API.
def test_call_openai():
    # Creating a fake OpenAI client.
    fake_client = MagicMock()

    # Preparing a fake JSON response.
    response_text = (
        '{"station_zone_profile": "transit_hub", '
        '"commuter_density_impact": "high", '
        '"enrichment_summary": "Near public transportation."}'
    )

    # Simulating the OpenAI response.
    fake_client.chat.completions.create.return_value.choices[
        0
    ].message.content = response_text

    # Replacing the real client with the fake client.
    with patch(
        "pipeline.enrich.llm_enrichment.get_openai_client",
        return_value=fake_client,
    ):
        result = call_openai("Profile Station One")

    # Checking the returned JSON text.
    assert result == response_text

    # Checking the selected model and JSON response format.
    request = fake_client.chat.completions.create.call_args
    assert request.kwargs["model"] == "gpt-4o-mini"
    assert request.kwargs["response_format"] == {"type": "json_object"}



# Testing the OpenAI enrichment entry point without real API calls.
def test_run_openai_enrichment():
    # Creating a fake Supabase client.
    fake_db = MagicMock()

    # Preparing a fake workflow result.
    expected_result = {
        "enriched": {},
        "errors": {},
    }

    # Replacing the real enrichment workflow with a mock.
    with patch(
        "pipeline.enrich.llm_enrichment.run_enrichment",
        return_value=expected_result,
    ) as mock_run:
        # Running the OpenAI enrichment entry point.
        result = run_openai_enrichment(fake_db)

        # Checking the arguments passed to the workflow.
        mock_run.assert_called_once_with(
            fake_db,
            call_openai,
            "station_enrichments",
        )

    # Checking that the workflow result is returned.
    assert result == expected_result
