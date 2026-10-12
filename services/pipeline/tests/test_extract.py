# Tests for the KAN-9 extract function
# Using mock data so the tests don't call the real API.

from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy import extract
#from services.pipeline.extract import extract

# Testing  API returns data successfully
def test_extract_success():
    # Fake response data
    mock_response = {
        "data": {
            "stations": [
                {
                    "station_id": "123",
                    "name": "Main Street Station"
                }
            ]
        }
    }
# creating fake http response object
    mock_http_response = MagicMock()
    mock_http_response.json.return_value = mock_response
    mock_http_response.raise_for_status.return_value = None

    
    with patch("pipeline.extract.extract.requests.get", return_value=mock_http_response) as mock_get:
        # Call extract function
        result = extract("https://example.com/station_information.json")
        assert result == mock_response["data"]
        mock_get.assert_called_once_with("https://example.com/station_information.json",  timeout=10)




# testing invalid input
def test_extract_invalid_input():
    pass

# Testing API returns empty response or missing data
def test_extract_empty_response():
    pass


# Testing API returns an error (e.g., 404, 500)
def test_extract_http_error():
    pass
