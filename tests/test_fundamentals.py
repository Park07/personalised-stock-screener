import unittest
from unittest.mock import patch, MagicMock
import json
import requests
from src.fundamentals import get_valuation, get_industry_pe

class TestValuationFunctions(unittest.TestCase):
    
    @patch('src.fundamentals.requests.get')
    def test_get_industry_pe_success(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"industry": "Technology", "pe": "25.6"},
            {"industry": "Healthcare", "pe": "18.3"}
        ]
        mock_get.return_value = mock_response
        
        # Execute function
        result = get_industry_pe("Technology", "2023-12-31")
        # Expected return: 25.6
        
        # Assertions
        self.assertEqual(result, 25.6)
        mock_get.assert_called_once()
        
    @patch('src.fundamentals.requests.get')
    def test_get_industry_pe_not_found(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"industry": "Technology", "pe": "25.6"}
        ]
        mock_get.return_value = mock_response
        
        # Execute function
        result = get_industry_pe("Finance", "2023-12-31")
        # Expected return: None (industry not found)
        
        # Assertions
        self.assertIsNone(result)
        

    @patch('src.fundamentals.requests.get')
    def test_get_industry_pe_http_error(self, mock_get):
        # Setup mock response to raise exception
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Client Error")
        mock_get.return_value = mock_response
        
        # Execute function & verify exception
        with self.assertRaises(requests.HTTPError):
            get_industry_pe("Technology", "2023-12-31")
        # Expected: HTTPError is raised
    

 

    @patch('src.fundamentals.get_industry_pe')
    @patch('src.fundamentals.requests.get')
    def test_get_valuation_success(self, mock_get, mock_get_industry_pe):
        # Setup mock responses for all API calls
        # 1. Ratios data
        ratios_response = MagicMock()
        ratios_response.raise_for_status.return_value = None
        ratios_response.json.return_value = [{
            "date": "2023-12-31",
            "priceEarningsRatio": 20.5,
            "priceEarningsToGrowthRatio": 1.8,
            "priceToSalesRatio": 3.2,
            "enterpriseValueMultiple": 15.6,
            "returnOnEquity": 0.21,
            "debtRatio": 0.35
        }]

   
        # 2. Key metrics data
        metrics_response = MagicMock()
        metrics_response.raise_for_status.return_value = None
        metrics_response.json.return_value = [{
            "enterpriseValueTTM": 1000000000,
            "freeCashFlowYieldTTM": 0.045
        }]
        
        # 3. Growth data
        growth_response = MagicMock()
        growth_response.raise_for_status.return_value = None
        growth_response.json.return_value = [{
            "revenueGrowth": 0.15,
            "epsgrowth": 0.18
        }]
        
        # 4. Profile data
        profile_response = MagicMock()
        profile_response.raise_for_status.return_value = None
        profile_response.json.return_value = [{
            "industry": "Technology"
        }]


        
        # Configure mock_get to return different responses based on URL
        def side_effect(*args, **kwargs):
            url = args[0]
            if "ratios" in url:
                return ratios_response
            elif "key-metrics" in url:
                return metrics_response
            elif "financial-growth" in url:
                return growth_response
            elif "profile" in url:
                return profile_response
            return MagicMock()
            
        mock_get.side_effect = side_effect
        
        # Mock industry PE
        mock_get_industry_pe.return_value = 22.5
        
        # Execute function
        result = get_valuation("AAPL")
        # Expected return:
        # {
        #     "pe": 20.5,
        #     "industry_pe": 22.5,
        #     "peg": 1.8,
        #     "ps": 3.2,
        #     "evToEbitda": 15.6,
        #     "roe": 0.21,
        #     "debtRatio": 0.35,
        #     "enterpriseValue": 1000000000,
        #     "freeCashFlowYield": 0.045,
        #     "revenueGrowth": 0.15,
        #     "epsGrowth": 0.18
        # }
        
        # Assertions
        self.assertEqual(result["pe"], 20.5)
        self.assertEqual(result["industry_pe"], 22.5)
        self.assertEqual(result["peg"], 1.8)
        self.assertEqual(result["ps"], 3.2)
        self.assertEqual(result["evToEbitda"], 15.6)
        self.assertEqual(result["roe"], 0.21)
        self.assertEqual(result["debtRatio"], 0.35)
        self.assertEqual(result["enterpriseValue"], 1000000000)
        self.assertEqual(result["freeCashFlowYield"], 0.045)
        self.assertEqual(result["revenueGrowth"], 0.15)
        self.assertEqual(result["epsGrowth"], 0.18)
        
        # Verify all API calls were made
        self.assertEqual(mock_get.call_count, 4)
        mock_get_industry_pe.assert_called_once_with("Technology", "2023-12-31")


    @patch('src.fundamentals.requests.get')
    def test_get_valuation_ratios_error(self, mock_get):
        # Setup mock response to fail on ratios data
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response
        
        # Execute function & verify exception
        with self.assertRaises(Exception) as context:
            get_valuation("AAPL")
        # Expected: Exception with message containing "Error fetching ratios data"
        
        self.assertTrue("Error fetching ratios data" in str(context.exception))
    
    @patch('src.fundamentals.requests.get')
    def test_get_valuation_empty_ratios(self, mock_get):
        # Setup mock response with empty ratios data
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        # Execute function & verify exception
        with self.assertRaises(Exception) as context:
            get_valuation("AAPL")
        # Expected: Exception with message "No ratio data returned"
        
        self.assertTrue("No ratio data returned" in str(context.exception))

if __name__ == '__main__':
    unittest.main()