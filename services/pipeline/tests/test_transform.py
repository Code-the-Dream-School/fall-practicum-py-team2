

from unittest import result

import pytest
from unittest.mock import MagicMock, patch
from pipeline.transform.transform_gold import transform_and_load_to_gold
from pathlib import Path


# Basic tests: Check sample data and transformation results


@pytest.fixture
def sample_stations():
    # Sample bike stations for transformation testing
    return [
        
        {
            # Station 101: 0% - empty
            "station_id": "101",
            "lat": 42.36,
            "lon": -71.06,
            "capacity": 10,
            "num_bikes_available": 0,
            "num_docks_available": 10,
        },

        {   # Station 102: 20% - low
            "station_id": "102",
            "lat": 42.37,
            "lon": -71.07,
            "capacity": 10,
            "num_bikes_available": 2,
            "num_docks_available": 8,
        },
        {   # Station 103: 50% - healthy
            "station_id": "103",
            "lat": 42.38,
            "lon": -71.08,
            "capacity": 10,
            "num_bikes_available": 5,
            "num_docks_available": 5,
        },
        {   # Station 104: 90% - full
            "station_id": "104",
            "lat": 42.39,
            "lon": -71.09,
            "capacity": 10,     
            "num_bikes_available": 9,
            "num_docks_available": 1,
        },
    ]

def test_sample_station_data(sample_stations):
    # Checking that our sample data is correct
    assert len(sample_stations) == 4
    assert sample_stations[0]["num_bikes_available"] == 0
    assert sample_stations[3]["num_docks_available"] == 1

# Testing successful transformation  
def test_transform_success(sample_stations):
    # Creating a fake Supabase connection
    fake_supabase = MagicMock()

    # Making the fake database return our sample stations
    fake_supabase.table.return_value.select.return_value.execute.return_value.data = sample_stations

    # Using fake credentials and a fake database connection
    with patch.dict("os.environ", {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-key",
    }):
        with patch(
            "pipeline.transform.transform_gold.create_client",
            return_value=fake_supabase,
        ):
            result = transform_and_load_to_gold()

    # Checking the transformed results
    assert len(result) == 4
    # assert result["score"].tolist() == [0.0, 0.2, 0.5, 0.9]
    # assert result["category"].tolist() == ["empty", "low", "healthy", "full"]
    assert result["availability"].tolist() == [0.0, 20.0, 50.0, 90.0]
    assert result["availability_status"].tolist() == ["empty", "low", "healthy", "full"]

# Edge case and data cleaning tests: Check empty or invalid data
# Testing  an empty database
def test_transform_empty_input():
    fake_supabase = MagicMock()

    # The fake database has no stations
    fake_supabase.table.return_value.select.return_value.execute.return_value.data = []

    with patch.dict("os.environ", {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-key",
    }):
        with patch(
            "pipeline.transform.transform_gold.create_client",
            return_value=fake_supabase,
        ):
            result = transform_and_load_to_gold()

    
    assert result.empty


# Data cleaning tests: Check how the transform function handles missing or invalid data
# Test a missing station ID
def test_transform_missing_station_id():
    # Create a fake Supabase connection
    fake_supabase = MagicMock()

    # Sample station without station_id
    invalid_stations = [
        {
            "lat": 42.36,
            "lon": -71.06,
            "capacity": 10,
            "num_bikes_available": 5,
            "num_docks_available": 5,
        }
    ]

    # Return invalid data from our fake database
    fake_supabase.table.return_value.select.return_value.execute.return_value.data = invalid_stations

    with patch.dict("os.environ", {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-key",
    }):
        with patch(
            "pipeline.transform.transform_gold.create_client",
            return_value=fake_supabase,
        ):
            # Checking that the function raises an error
            with pytest.raises(KeyError):
                transform_and_load_to_gold()

#Testing a missing ID among valid stations
def test_transform_skips_missing_station_id(sample_stations):
    fake_supabase = MagicMock()

    # invalid station
    invalid_station = {
        "station_id": None,
        "lat": 42.40,
        "lon": -71.10,
        "capacity": 10,
        "num_bikes_available": 5,
        "num_docks_available": 5,
    }
    ## Combining 4 valid stations with 1 invalid station
    stations = sample_stations + [invalid_station]

    fake_supabase.table.return_value.select.return_value.execute.return_value.data = stations

    with patch.dict("os.environ", {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-key",
    }):
        with patch(
            "pipeline.transform.transform_gold.create_client",
            return_value=fake_supabase,
        ):
            result = transform_and_load_to_gold()

    # Only the four valid stations should remain
    assert len(result) == 4
    assert result["station_id"].tolist() == ["101", "102", "103", "104"]

# Testing a missing GPS coordinate
def test_transform_skips_missing_lat(sample_stations):
    fake_supabase = MagicMock()

    # Create a station with missing latitude
    invalid_station = {
        "station_id": "105",
        "lat": None,
        "lon": -71.10,
        "capacity": 10,
        "num_bikes_available": 5,
        "num_docks_available": 5,
    }

    # Combining 4 valid stations with 1 invalid station
    stations = sample_stations + [invalid_station]

    # Return our sample data from the fake database
    fake_supabase.table.return_value.select.return_value.execute.return_value.data = stations

    with patch.dict("os.environ", {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-key",
    }):
        with patch(
            "pipeline.transform.transform_gold.create_client",
            return_value=fake_supabase,
        ):
            result = transform_and_load_to_gold()

    # Checking that only the 4 valid stations remain
    assert len(result) == 4
    assert "105" not in result["station_id"].tolist()

# data cleaning and numeric conversion.
# Testing an invalid bike count(unknown)

def test_transform_invalid_bike_count():
    fake_supabase = MagicMock()

    # Station with an invalid bike count
    invalid_stations = [
        {
            "station_id": "105",
            "lat": 42.40,
            "lon": -71.10,
            "capacity": 10,
            "num_bikes_available": "unknown",
            "num_docks_available": 10,
        }
    ]

    # Return the station from our fake database
    fake_supabase.table.return_value.select.return_value.execute.return_value.data = invalid_stations

    with patch.dict("os.environ", {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-key",
    }):
        with patch(
            "pipeline.transform.transform_gold.create_client",
            return_value=fake_supabase,
        ):
            result = transform_and_load_to_gold()

    # Check that the invalid bike count becomes 0
    assert result["num_bikes_available"].iloc[0] == 0
    assert result["availability"].iloc[0] == 0.0
    assert result["availability_status"].iloc[0] == "empty"

# Testing the rolling average

def test_transform_rolling_average():
    fake_supabase = MagicMock()

    # Using 3 observations from the same station
    stations = [
        {
            "station_id": "101",
            "lat": 42.36,
            "lon": -71.06,
            "capacity": 10,
            "num_bikes_available": 2,
            "num_docks_available": 8,
            "collected_at": "2026-10-24T08:00:00",
        },
        {
            "station_id": "101",
            "lat": 42.36,
            "lon": -71.06,
            "capacity": 10,
            "num_bikes_available": 5,
            "num_docks_available": 5,
            "collected_at": "2026-10-24T08:05:00",
        },
        {
            "station_id": "101",
            "lat": 42.36,
            "lon": -71.06,
            "capacity": 10,
            "num_bikes_available": 8,
            "num_docks_available": 2,
            "collected_at": "2026-10-24T08:10:00",
        },
    ]

    # Return our sample data from the fake database
    fake_supabase.table.return_value.select.return_value.execute.return_value.data = stations

    with patch.dict("os.environ", {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-key",
    }):
        with patch(
            "pipeline.transform.transform_gold.create_client",
            return_value=fake_supabase,
        ):
            result = transform_and_load_to_gold()

    # Check availability percentages
    assert result["availability"].tolist() == [20.0, 50.0, 80.0]

    # Check the rolling average calculation
    assert result["rolling_avg_score"].tolist() == [20.0, 35.0, 50.0]

# Testing missing database credentials
def test_transform_missing_credentials():
    # without credentials
    with patch.dict("os.environ", {
        "SUPABASE_URL": "",
        "SUPABASE_KEY": "",
    }):
        with patch("pipeline.transform.transform_gold.load_dotenv"):
            # Check that the function raises an error
            with pytest.raises(ValueError):
                transform_and_load_to_gold()