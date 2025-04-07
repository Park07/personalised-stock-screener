import unittest
from unittest.mock import patch, MagicMock
import json
import requests


from src.fundamentals import get_valuation

# --- Sample Mock Data (Mimicking FMP API Responses) -
# Since unit test cannot work on live FMP API data, we need to isolate and
# test on deterministic state. which is only possible if we create fake mock version
# this will allow to test the logic and calculation is valid or not.

# Represents a successful response from /ratios-ttm/FAKE
MOCK_RATIOS_TTM_SUCCESS = [{
    "symbol": "FAKE",
    "priceEarningsRatioTTM": 20.0,
    "priceEarningsToGrowthRatioTTM": 1.5,
    "priceToBookRatioTTM": 4.0,
    "priceToSalesRatioTTM": 2.5,
    "enterpriseValueMultipleTTM": 15.0,
    "earningsYieldTTM": 0.05, 
    "freeCashFlowYieldTTM": None 
    
}]

# Represents a successful response from /key-metrics-ttm/FAKE
MOCK_KEY_METRICS_TTM_SUCCESS = [{
    "symbol": "FAKE",
    "enterpriseValueTTM": 5000000000.0,
    "freeCashFlowYieldTTM": 0.045 
}]

# Represents response when PE is zero
MOCK_RATIOS_TTM_ZERO_PE = [{
    "symbol": "FAKE",
    "priceEarningsRatioTTM": 0.0,
    "priceEarningsToGrowthRatioTTM": None,
    "priceToBookRatioTTM": 1.0,
    "priceToSalesRatioTTM": 0.5,
    "enterpriseValueMultipleTTM": -10.0,
    "earningsYieldTTM": None
}]


class TestGetValuation(unittest.TestCase):

    # Helper function to create a mock response object
    def _create_mock_response(self, json_data, status_code=200, raise_for_status_exception=None):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        if raise_for_status_exception:
            mock_resp.raise_for_status.side_effect = raise_for_status_exception
        else:
            mock_resp.raise_for_status.return_value = None
        return mock_resp

    @patch('src.fundamentals.requests.get')
    def test_get_valuation_success(self, mock_get):
        """Tests successful retrieval and processing of valuation data."""

        def side_effect_func(url, *args, **kwargs):
            if "ratios-ttm" in url:
                return self._create_mock_response(MOCK_RATIOS_TTM_SUCCESS)
            elif "key-metrics-ttm" in url:
                return self._create_mock_response(MOCK_KEY_METRICS_TTM_SUCCESS)
            else:
                # If an unexpected URL is called, raise an error
                raise ValueError(f"Unexpected URL called in mock: {url}")

        mock_get.side_effect = side_effect_func

        # Call the function under test
        ticker = "FAKE"
        result = get_valuation(ticker)

        # Expected output based on mock data
        expected = {
            "pe": 20.0,
            "peg": 1.5,
            "pb": 4.0,
            "ps": 2.5,
            "evToEbitda": 15.0,
            "enterpriseValue": 5000000000.0,
            "earningsYield": 1 / 20.0, # Calculated
            "freeCashFlow_yield": 0.045 
        }




    @patch('src.fundamentals.requests.get')
    def test_get_valuation_ratios_api_error(self, mock_get):
        """Tests error handling when the key ratios call fails."""

        # Configure mock to raise an HTTP error for the ratios call
        mock_get.return_value = self._create_mock_response(
            None, status_code=500, raise_for_status_exception=requests.exceptions.HTTPError("Server Error")
        )

        # Assert that calling the function raises the expected Exception
        with self.assertRaises(Exception) as cm:
            get_valuation("FAKE")



    @patch('src.fundamentals.requests.get')
    def test_get_valuation_key_metrics_api_error(self, mock_get):
        """Tests handling when key metrics fails but ratios succeed."""

        # Configure side effect: success for ratios, error for key metrics
        def side_effect_func(url, *args, **kwargs):
            if "ratios-ttm" in url:
                return self._create_mock_response(MOCK_RATIOS_TTM_SUCCESS)
            elif "key-metrics-ttm" in url:
                # Simulate failure for key metrics call
                return self._create_mock_response(None, 500, requests.exceptions.HTTPError("Metrics Server Error"))
            else: raise ValueError(f"Unexpected URL: {url}")

        mock_get.side_effect = side_effect_func

        ticker = "FAKE"
        result = get_valuation(ticker)

        # Expected output: ratio data should be present, metrics data should be missing (None)
        expected = {
            "pe": 20.0,
            "peg": 1.5,
            "pb": 4.0,
            "ps": 2.5,
            "evToEbitda": 15.0,
            "enterpriseValue": None, # Failed fetch
            "earningsYield": 1 / 20.0,
            "freeCashFlow_yield": None # Failed fetch (or maybe from ratios if that mock had it)
        }

        self.assertDictEqual(result, expected)
        self.assertEqual(mock_get.call_count, 2) # Both APIs were called


    @patch('src.fundamentals.requests.get')
    def test_get_valuation_missing_keys(self, mock_get):
        """Tests handling when API response is missing expected keys."""

         # Mock data missing PEG and EV/EBITDA
        mock_ratios_missing = [{ "priceEarningsRatioTTM": 25.0, "priceToBookRatioTTM": 3.0, "priceToSalesRatioTTM": 2.0 }]
        mock_metrics_missing = [{ "freeCashFlowYieldTTM": 0.03 }] # Missing enterpriseValueTTM

        def side_effect_func(url, *args, **kwargs):
            if "ratios-ttm" in url: 
                return self._create_mock_response(mock_ratios_missing)
            elif "key-metrics-ttm" in url: 
                return self._create_mock_response(mock_metrics_missing)
            else: 
                raise ValueError(f"Unexpected URL: {url}")

        mock_get.side_effect = side_effect_func

        result = get_valuation("FAKE")

        expected = {
            "pe": 25.0,
            "peg": None, # Should be None as key is missing
            "pb": 3.0,
            "ps": 2.0,
            "evToEbitda": None, # Should be None as key is missing
            "enterpriseValue": None, # Should be None as key is missing
            "earningsYield": 1 / 25.0,
            "freeCashFlow_yield": 0.03
        }
        self.assertDictEqual(result, expected)


    @patch('src.fundamentals.requests.get')
    def test_get_valuation_zero_pe(self, mock_get):
        """Tests earningsYield calculation when PE ratio is zero."""

        def side_effect_func(url, *args, **kwargs):
            if "ratios-ttm" in url: 
                return self._create_mock_response(MOCK_RATIOS_TTM_ZERO_PE)
            elif "key-metrics-ttm" in url: 
                return self._create_mock_response(MOCK_KEY_METRICS_TTM_SUCCESS) # Assuming metrics succeed
            else: 
                raise ValueError(f"Unexpected URL: {url}")

        mock_get.side_effect = side_effect_func

        result = get_valuation("FAKE")

        self.assertEqual(result["pe"], 0.0)
        self.assertIsNone(result["earningsYield"], "Earnings yield should be None when PE is 0")


# Allows running the tests directly from the command line
if __name__ == '__main__':
    unittest.main()