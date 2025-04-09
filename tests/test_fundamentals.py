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
        
    
        
if __name__ == '__main__':
    unittest.main()