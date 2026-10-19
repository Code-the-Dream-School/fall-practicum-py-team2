import pytest


@pytest.fixture
def sample_stations():
    # Sample station data for testing
    return [
        {"station_id": "101", "bikes": 0, "docks": 10},
        {"station_id": "102", "bikes": 2, "docks": 8},
        {"station_id": "103", "bikes": 5, "docks": 5},
        {"station_id": "104", "bikes": 9, "docks": 1},
    ]


def test_sample_station_data(sample_stations):
    # Check that our sample data is correct
    assert len(sample_stations) == 4
    assert sample_stations[0]["bikes"] == 0
    assert sample_stations[3]["docks"] == 1