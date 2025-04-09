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

# Tests for get_ratios, get_key_metrics, get_growth, get_profile
class TestBasicFunctions(unittest.TestCase):
    @patch('src.fundamentals.fetch_first_item')
    def test_get_ratios_success(self, mock_fetch):
        mock_fetch.return_value = {"pe": 20, "debtRatio": 0.5}
        result = get_ratios("AAPL")
        self.assertEqual(result, {"pe": 20, "debtRatio": 0.5})
        args, _ = mock_fetch.call_args
        self.assertIn("AAPL", args[0])
        self.assertIn("apikey", args[0])
    
    # enterprise Value
    @patch('src.fundamentals.fetch_first_item')
    def test_get_key_metrics_success(self, mock_fetch):
        mock_fetch.return_value = {"enterpriseValue": 1000000}
        result = get_key_metrics("AAPL")
        self.assertEqual(result, {"enterpriseValue": 1000000})
    
    # revenue Growth
    @patch('src.fundamentals.fetch_first_item')
    def test_get_growth_success(self, mock_fetch):
        mock_fetch.return_value = {"revenueGrowth": 0.15}
        result = get_growth("AAPL")
        self.assertEqual(result, {"revenueGrowth": 0.15})
    
    # industry?
    @patch('src.fundamentals.fetch_first_item')
    def test_get_profile_success(self, mock_fetch):
        mock_fetch.return_value = {"industry": "Technology"}
        result = get_profile("AAPL")
        self.assertEqual(result, {"industry": "Technology"})
    

    @patch('src.fundamentals.fetch_first_item')
    def test_get_profile_error(self, mock_fetch):
        # Simulate a case where fetch_first_item returns None. This should lead to a ValueError.
        mock_fetch.return_value = None
        with self.assertRaises(ValueError):
            get_profile("AAPL")


if __name__ == '__main__':
    unittest.main()