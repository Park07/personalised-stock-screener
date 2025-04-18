import unittest
from unittest.mock import patch
from src.fundamentals import (
    get_ratios,
    get_key_metrics,
    get_growth,
    get_profile,
    yahoo_sector_pe,       
    get_valuation
)

class TestGetValuation(unittest.TestCase):

    # ---------------------------- SUCCESS PATH ----------------------------
    @patch('src.fundamentals.get_ratios')
    @patch('src.fundamentals.get_key_metrics')
    @patch('src.fundamentals.get_growth')
    @patch('src.fundamentals.get_profile')
    @patch('src.fundamentals.yahoo_sector_pe') # Ensure this path is correct
    def test_get_valuation_success(
        self,
        mock_sector_pe, mock_profile, mock_growth,
        mock_key_metrics, mock_ratios
    ):

        # Mock return values setup
        mock_ratios.return_value = {
            "date": "2023-12-31", "priceEarningsRatio": 20.5,
            "priceEarningsToGrowthRatio": 1.5, "priceToSalesRatio": 3.2,
            "enterpriseValueMultiple": 12.1, "returnOnEquity": 0.15,
            "debtRatio": 0.35
        }
        mock_key_metrics.return_value = {
            "enterpriseValue": 1_000_000_000, "freeCashFlowYield": 0.05
        }
        mock_growth.return_value = {
            "revenueGrowth": 0.12, "epsgrowth": 0.08
        }
        mock_profile.return_value = {
             # Using 'sector' key to match the corrected get_valuation
            "sector": "Information Technology"
        }
        mock_sector_pe.return_value = 22.3

        # Call the function
        result = get_valuation("AAPL")

        # Assertions
        self.assertEqual(result["pe"], 20.5)
        self.assertEqual(result["sector_pe"], 22.3) # This is the key assertion
        self.assertEqual(result["peg"], 1.5)
        self.assertEqual(result["ps"], 3.2)
        self.assertEqual(result["roe"], 0.15)
        self.assertEqual(result["debtRatio"], 0.35)
        self.assertEqual(result["enterpriseValue"], 1_000_000_000)
        self.assertEqual(result["freeCashFlowYield"], 0.05)
        self.assertEqual(result["revenueGrowth"], 0.12)
        self.assertEqual(result["epsGrowth"], 0.08)

        # verify calls
        mock_ratios.assert_called_once_with("AAPL")
        mock_key_metrics.assert_called_once_with("AAPL")
        mock_growth.assert_called_once_with("AAPL")
        mock_profile.assert_called_once_with("AAPL")
        # Verify yahoo_sector_pe was called with the correct sector from the mock profile
        mock_sector_pe.assert_called_once_with("Information Technology")



    # --------------------------- FAILURE PATH -----------------------------
    @patch('src.fundamentals.get_ratios')
    @patch('src.fundamentals.get_key_metrics')
    @patch('src.fundamentals.get_growth')
    @patch('src.fundamentals.get_profile')
    def test_get_valuation_missing_sector_pe(
        self, mock_profile, mock_growth, mock_key_metrics, mock_ratios
    ):

        mock_ratios.return_value = {
            "date": "2023-12-31",
            "priceEarningsRatio": 20.5,
            "priceEarningsToGrowthRatio": 1.5,
            "priceToSalesRatio": 3.2,
            "enterpriseValueMultiple": 12.1,
            "returnOnEquity": 0.15,
            "debtRatio": 0.35
        }
        mock_key_metrics.return_value = {
            "enterpriseValue": 1_000_000_000,
            "freeCashFlowYield": 0.05
        }
        mock_growth.return_value = {
            "revenueGrowth": 0.12,
            "epsgrowth": 0.08
        }
        mock_profile.return_value = {
            "sector": "Information Technology"
        }

        with patch('src.fundamentals.yahoo_sector_pe',
                   side_effect=Exception("API error")):
            result = get_valuation("AAPL")
            self.assertIsNone(result["sector_pe"])
            self.assertEqual(result["pe"], 20.5)


if __name__ == '__main__':
    unittest.main()
