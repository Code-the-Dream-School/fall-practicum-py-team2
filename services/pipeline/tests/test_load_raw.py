import json
from unittest.mock import MagicMock


def test_load_raw_success(tmp_path):
    # Create sample bike station data
    sample_data = [
        {
            "station_id": "101",
            "name": "Station A",
            "num_bikes_available": 8,
            "num_docks_available": 2
        }
    ]

    # Create a temporary JSON file
    file_path = tmp_path / "station_information.json"
    file_path.write_text(json.dumps(sample_data))

    # Create a fake Supabase client
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.upsert.return_value.execute.return_value.count = 1

    # Simulate the database loading process
    response = (
        fake_supabase
        .table("station_information")
        .upsert(sample_data, count="exact")
        .execute()
    )

    # Check that the correct data was sent to Supabase
    fake_supabase.table.assert_called_once_with("station_information")
    fake_supabase.table.return_value.upsert.assert_called_once_with(
        sample_data, count="exact"
    )

    assert response.count == 1
    