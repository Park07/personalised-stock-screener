import unittest
from unittest.mock import patch, MagicMock
import requests
import json
from src.fundamentals import (
    fetch_first_item,
    get_ratios,
    get_key_metrics,
    get_growth,
    get_profile,
    get_industry_pe,
    get_valuation
)

# Tests for fetch_first_item
class TestFetchFirstItem(unittest.TestCase):
    @patch('src.fundamentals.requests.get')
    def test_fetch_first_item_success(self, mock_get):
        # Setup a successful response with non-empty JSON list
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"key": "value"}]
        mock_get.return_value = mock_response
        
        result = fetch_first_item("http://test.com", "Test error")
        self.assertEqual(result, {"key": "value"})
        mock_get.assert_called_once_with("http://test.com")
    
    # empty response
    @patch('src.fundamentals.requests.get')
    def test_fetch_first_item_empty_response(self, mock_get):
        # Setup a response that returns an empty list
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            fetch_first_item("http://test.com", "Test error")
        self.assertTrue("Test error" in str(context.exception))
    
    # http erro should generate "Warning empty response returned"
    @patch('src.fundamentals.requests.get')
    def test_fetch_first_item_http_error(self, mock_get):
        # Setup a 404 HTTP error scenario
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        # When default is provided, the function should return that default
        result = fetch_first_item("http://test.com", "Test error", default={"default": True})
        self.assertEqual(result, {"default": True})
    
    #  Returns Invalid JSON output
    @patch('src.fundamentals.requests.get')
    def test_fetch_first_item_json_decode_error(self, mock_get):
        # Setup a bad JSON decode scenario
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        result = fetch_first_item("http://test.com", "Test error", default={"default": True})
        self.assertEqual(result, {"default": True})


if __name__ == '__main__':
    unittest.main()