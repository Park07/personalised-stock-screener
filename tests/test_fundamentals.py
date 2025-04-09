import unittest
from unittest.mock import patch, MagicMock
import requests
from src.fundamentals import get_industry_pe, get_valuation

class TestValuationFunctions(unittest.TestCase):

    @patch('src.fundamentals.requests.get')
    def test_get_industry_pe_success(self, mock_get):
        # Setup mock response for a successful industry PE lookup
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"industry": "Technology", "pe": "25.6"},
            {"industry": "Healthcare", "pe": "18.3"}
        ]
        mock_get.return_value = mock_response

        result = get_industry_pe("Technology", "2023-12-31")
        self.assertEqual(result, 25.6)
        mock_get.assert_called_once()

    @patch('src.fundamentals.requests.get')
    def test_get_industry_pe_not_found(self, mock_get):
        # Setup mock response where the requested industry is not present
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"industry": "Technology", "pe": "25.6"}
        ]
        mock_get.return_value = mock_response

        result = get_industry_pe("Finance", "2023-12-31")
        self.assertIsNone(result)

    @patch('src.fundamentals.requests.get')
    def test_get_industry_pe_http_error(self, mock_get):
        # Setup mock to simulate an HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Client Error")
        mock_get.return_value = mock_response

        with self.assertRaises(requests.HTTPError):
            get_industry_pe("Technology", "2023-12-31")

if __name__ == '__main__':
    unittest.main()