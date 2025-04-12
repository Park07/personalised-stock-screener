import unittest
from unittest.mock import patch, MagicMock
import json
import requests
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

# Tests for get_industry_pe
class TestIndustryPE(unittest.TestCase):
    @patch('src.fundamentals.requests.get')
    def test_get_industry_pe_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"industry": "Other", "pe": 15.0},
            {"industry": "Technology", "pe": 25.0}
        ]
        mock_get.return_value = mock_response

        result = get_industry_pe("Technology", "2023-12-31")
        self.assertEqual(result, 25.0)
        args, _ = mock_get.call_args
        self.assertIn("date=2023-12-31", args[0])

    @patch('src.fundamentals.requests.get')
    def test_get_industry_pe_industry_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"industry": "Other", "pe": 15.0}]
        mock_get.return_value = mock_response

        result = get_industry_pe("Technology", "2023-12-31")
        self.assertIsNone(result)

    @patch('src.fundamentals.requests.get')
    def test_get_industry_pe_http_error(self, mock_get):
        # In this test, let the HTTP error propagate.
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        with self.assertRaises(requests.HTTPError):
            get_industry_pe("Technology", "2023-12-31")

# Tests for get_valuation
class TestValuation(unittest.TestCase):
    @patch('src.fundamentals.get_ratios')
    @patch('src.fundamentals.get_key_metrics')
    @patch('src.fundamentals.get_growth')
    @patch('src.fundamentals.get_profile')
    @patch('src.fundamentals.get_industry_pe')
    def test_get_valuation_success(self, mock_industry_pe, mock_profile,
                                   mock_growth, mock_metrics, mock_ratios):
        mock_ratios.return_value = {
            "date": "2023-12-31",
            "priceEarningsRatio": 20.5,
            "priceEarningsToGrowthRatio": 1.8,
            "priceToSalesRatio": 3.2,
            "enterpriseValueMultiple": 15.6,
            "returnOnEquity": 0.21,
            "debtRatio": 0.35
        }
        mock_metrics.return_value = {
            "enterpriseValue": 1000000000,
            "freeCashFlowYield": 0.045
        }
        mock_growth.return_value = {"revenueGrowth": 0.15, "epsgrowth": 0.18}
        mock_profile.return_value = {"industry": "Technology"}
        mock_industry_pe.return_value = 22.3

        result = get_valuation("AAPL")
        self.assertEqual(result["pe"], 20.5)
        self.assertEqual(result["industry_pe"], 22.3)
        self.assertEqual(result["peg"], 1.8)
        self.assertEqual(result["ps"], 3.2)
        self.assertEqual(result["evToEbitda"], 15.6)
        self.assertEqual(result["roe"], 0.21)
        self.assertEqual(result["debtRatio"], 0.35)
        self.assertEqual(result["enterpriseValue"], 1000000000)
        self.assertEqual(result["freeCashFlowYield"], 0.045)
        self.assertEqual(result["revenueGrowth"], 0.15)
        self.assertEqual(result["epsGrowth"], 0.18)

    @patch('src.fundamentals.get_ratios')
    def test_get_valuation_ratios_error(self, mock_ratios):
        mock_ratios.side_effect = Exception("Ratios error")
        with self.assertRaises(Exception):
            get_valuation("AAPL")

    @patch('src.fundamentals.get_ratios')
    @patch('src.fundamentals.get_key_metrics')
    @patch('src.fundamentals.get_growth')
    @patch('src.fundamentals.get_profile')
    def test_get_valuation_no_industry_pe(self, mock_profile, mock_growth,
                                          mock_metrics, mock_ratios):
        mock_ratios.return_value = {
            "date": "2023-12-31",
            "priceEarningsRatio": 20.5,
            "priceEarningsToGrowthRatio": 1.8,
            "priceToSalesRatio": 3.2,
            "enterpriseValueMultiple": 15.6,
            "returnOnEquity": 0.21,
            "debtRatio": 0.35
        }
        mock_metrics.return_value = {
            "enterpriseValue": 1000000000,
            "freeCashFlowYield": 0.045
        }
        mock_growth.return_value = {"revenueGrowth": 0.15, "epsgrowth": 0.18}
        # Profile returns no industry
        mock_profile.return_value = {}
        result = get_valuation("AAPL")
        self.assertIsNone(result["industry_pe"])


if __name__ == '__main__':
    unittest.main()
