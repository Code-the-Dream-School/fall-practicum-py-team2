# KAN-9: Unit tests for the extract() function.
# These tests use mock data instead of calling the real API.
#
# NOTE: Waiting for the KAN-8 extract.py update.
# Currently, importing extract.py triggers real API requests.
# Do not run pytest until the import issue is fixed.

from unittest.mock import patch, MagicMock
import pytest
import requests

from pipeline.extract.extract import extract

# Testing  API returns data successfully
def test_extract_success():
    # Fake response data
    mock_response = {
        "data": {
            "stations": [
                {
                    "station_id": "123",
                    "name": "Wonderland Station"
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
    invalid_url = "not-a-valid-url"
    with patch(
        "pipeline.extract.extract.requests.get",
        side_effect=requests.exceptions.MissingSchema(
            "Invalid URL: No scheme supplied")):
        with pytest.raises(requests.exceptions.MissingSchema):
            extract(invalid_url)
        



# # Testing API returns empty data
def test_extract_empty_response():
    # Fake API response with empty data
    mock_response = {
        "data": {}
    }

    # Creating fake HTTP response
    mock_http_response = MagicMock()
    mock_http_response.json.return_value = mock_response
    mock_http_response.raise_for_status.return_value = None

    # Replacing the real API request with our fake response
    with patch(
        "pipeline.extract.extract.requests.get",
        return_value=mock_http_response) as mock_get:

        # Calling extract function
        result = extract("https://example.com/station_information.json")

        # Checking that the returned data is empty
        assert result == {}

        # Checking that the API was called only once
        mock_get.assert_called_once_with(
            "https://example.com/station_information.json", timeout=10)



# Testing API returns an error (e.g., 404, 500)
def test_extract_http_error():
    # Creating  fake HTTP response
    mock_http_response = MagicMock()

    # Simulating a HTTP 500 server error
    mock_http_response.raise_for_status.side_effect = (
    requests.exceptions.HTTPError("500 Server Error"))
    # Replacing the real API request with our fake response
    with patch(
        "pipeline.extract.extract.requests.get",
        return_value=mock_http_response) as mock_get:

        # Checking that extract() raises an HTTPError
        with pytest.raises(requests.exceptions.HTTPError):
            extract("https://example.com/station_information.json")

        # Checking that the request was called once
        mock_get.assert_called_once_with(
        "https://example.com/station_information.json", timeout=10)

# Testing API returns a timeout error
def test_extract_timeout():
    # Simulating an API request that times out
    with patch(
        "pipeline.extract.extract.requests.get",
        side_effect=requests.exceptions.Timeout("Request timed out")) as mock_get:

        # Checking that extract() raises a Timeout exception
        with pytest.raises(requests.exceptions.Timeout):
            extract("https://example.com/station_information.json")

        # Verifying the request was called once
        mock_get.assert_called_once_with(
            "https://example.com/station_information.json", timeout=10)


# # Testing API returns a response without the expected "data" key
def test_extract_missing_data():
    # Fake API response without the "data" key
    mock_response = {}

    # Create a fake HTTP response
    mock_http_response = MagicMock()
    mock_http_response.json.return_value = mock_response
    mock_http_response.raise_for_status.return_value = None
    # Replace the real API request with our fake response
    with patch(
        "pipeline.extract.extract.requests.get",
        return_value=mock_http_response
    ) as mock_get:

        # Check that extract() raises a KeyError
        with pytest.raises(KeyError):
            extract("https://example.com/station_information.json")

        # Check that the request was called once
        mock_get.assert_called_once_with(
            "https://example.com/station_information.json",
            timeout=10
        )