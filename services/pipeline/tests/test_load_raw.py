import json
import pytest
from unittest.mock import MagicMock

from pipeline.load.load_raw import load_raw

# checking the behavior of load_raw() when provided with a valid JSON file containing station records
def test_load_raw_success(tmp_path):
    # Create sample station data
    sample_data = [
        {
            "station_id": "123",
            "name": "North Station", 
            "num_bikes_available": 8,
            "num_docks_available": 2,
        }
    ]

    # Create a temporary JSON file
    file_path = tmp_path / "station_information.json"
    file_path.write_text(json.dumps(sample_data))

    # Create a fake Supabase client
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.upsert.return_value.execute.return_value.count = 1

    # Call Gaby's actual function
    load_raw(fake_supabase, str(file_path), "station_information")

    # Check that the correct table was selected
    fake_supabase.table.assert_called_once_with("station_information")

    # Check that the correct data was sent
    fake_supabase.table.return_value.upsert.assert_called_once_with(
        sample_data,
        count="exact",
    )

    # Check that the database operation was executed
    fake_supabase.table.return_value.upsert.return_value.execute.assert_called_once()

# checking the behavior of load_raw() when provided with an empty list of station records
def test_load_raw_empty_input(tmp_path):
    # Create an empty list of station records
    sample_data = []
    
    # Save the empty list in a temporary JSON file
    file_path = tmp_path / "empty_stations.json"
    file_path.write_text(json.dumps(sample_data))
    
    # Create a fake Supabase client
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.upsert.return_value.execute.return_value.count = 0
    
    # Calling load_raw() function
    result = load_raw(fake_supabase, str(file_path), "station_information")

    # Checking nothing was sent to Supabase and 0 rows were reported
    assert result == 0

    fake_supabase.table.return_value.upsert.assert_not_called()

# checking the behavior of load_raw() when provided with a valid JSON file containing station records, and calling it twice
def test_load_raw_twice(tmp_path):
    # Create one station record
    sample_data = [
        {
            "station_id": "101",
            "name": "Station A",
            "num_bikes_available": 8,
            "num_docks_available": 2,
        }
    ]

    # Create temporary JSON file
    file_path = tmp_path / "stations.json"
    file_path.write_text(json.dumps(sample_data))

    # Create fake Supabase client
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.upsert.return_value.execute.return_value.count = 1

    # Load the same file twice
    load_raw(fake_supabase, str(file_path), "station_information")
    load_raw(fake_supabase, str(file_path), "station_information")

    # Verifying upsert was called twice
    assert fake_supabase.table.return_value.upsert.call_count == 2

    # Verifying both calls sent the same data
    for call in fake_supabase.table.return_value.upsert.call_args_list:
        assert call.args == (sample_data,)
        assert call.kwargs == {"count": "exact"}

# checking the behavior of load_raw() with a missing JSON file( missing closing })
def test_load_raw_missing_file(tmp_path):
    # Create a path to a file that does not exist
    file_path = tmp_path / "missing_stations.json"

    # Create a fake Supabase client
    fake_supabase = MagicMock()

    # Expect a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        load_raw(
            fake_supabase,
            str(file_path),
            "station_information"
        )

    # Verify that Supabase was not called
    fake_supabase.table.assert_not_called()
# testing the behavior of load_raw() with a malformed JSON file
def test_load_raw_malformed_json(tmp_path):
    # Create a temporary file with invalid JSON
    file_path = tmp_path / "invalid_stations.json"
    file_path.write_text('{"station_id": "101",')

    # Create a fake Supabase client
    fake_supabase = MagicMock()

    # Running load_raw function
    with pytest.raises(json.JSONDecodeError):
        load_raw(
            fake_supabase,
            str(file_path),
            "station_information"
        )

    # Verify no database operation was attempted
    fake_supabase.table.assert_not_called()

# Testing the behavior of load_raw() with a missing station_id
def test_load_raw_missing_station_id(tmp_path):
    # Create a station record without station_id
    sample_data = [
        {
            "name": "Station A",
            "num_bikes_available": 8,
            "num_docks_available": 2,
        }
    ]

    # Create a temporary JSON file
    file_path = tmp_path / "missing_station_id.json"
    file_path.write_text(json.dumps(sample_data))

    # Create a fake Supabase client
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.upsert.return_value.execute.return_value.count = 1

    # Calling load_raw function
    load_raw(
        fake_supabase,
        str(file_path),
        "station_information"
    )

    # Check that invalid data was not sent to Supabase
    fake_supabase.table.return_value.upsert.assert_not_called()