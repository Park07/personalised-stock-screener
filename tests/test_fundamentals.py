import unittest
from unittest.mock import patch, MagicMock
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

class TestGetValuation(unittest.TestCase):
    @patch('src.fundamentals.get_ratios')
    @patch('src.fundamentals.get_key_metrics')
    @patch('src.fundamentals.get_growth')
    @patch('src.fundamentals.get_profile')
    @patch('src.fundamentals.get_industry_pe')
    def test_get_valuation_success(self, mock_industry_pe, mock_profile, mock_growth,
                                  mock_key_metrics, mock_ratios):
        # mock values idk

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
            "enterpriseValue": 1000000000,
            "freeCashFlowYield": 0.05
        }
        mock_growth.return_value = {
            "revenueGrowth": 0.12,
            "epsgrowth": 0.08
        }
        mock_profile.return_value = {
            "industry": "Technology"
        }
        mock_industry_pe.return_value = 22.3

        result = get_valuation("AAPL")


        self.assertEqual(result["pe"], 20.5)
        self.assertEqual(result["industry_pe"], 22.3)
        self.assertEqual(result["peg"], 1.5)
        self.assertEqual(result["ps"], 3.2)
        self.assertEqual(result["evToEbitda"], 12.1)
        self.assertEqual(result["roe"], 0.15)
        self.assertEqual(result["debtRatio"], 0.35)
        self.assertEqual(result["enterpriseValue"], 1000000000)
        self.assertEqual(result["freeCashFlowYield"], 0.05)
        self.assertEqual(result["revenueGrowth"], 0.12)
        self.assertEqual(result["epsGrowth"], 0.08)
        # Check function calls
        mock_ratios.assert_called_once_with("AAPL")
        mock_key_metrics.assert_called_once_with("AAPL")
        mock_growth.assert_called_once_with("AAPL")
        mock_profile.assert_called_once_with("AAPL")
        mock_industry_pe.assert_called_once_with("Technology", "2023-12-31")
    # industry pe not exist
    @patch('src.fundamentals.get_ratios')
    @patch('src.fundamentals.get_key_metrics')
    @patch('src.fundamentals.get_growth')
    @patch('src.fundamentals.get_profile')
    def test_get_valuation_missing_industry_pe(self, mock_profile, mock_growth,
                                             mock_key_metrics, mock_ratios):
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
            "enterpriseValue": 1000000000,
            "freeCashFlowYield": 0.05
        }
        mock_growth.return_value = {
            "revenueGrowth": 0.12,
            "epsgrowth": 0.08
        }
        mock_profile.return_value = {
            "industry": "Technology"
        }

        # throws exception in case industry pe doesnt exist otherwise usual checking
        with patch('src.fundamentals.get_industry_pe', side_effect=Exception("API error")):
            result = get_valuation("AAPL")
            self.assertIsNone(result["industry_pe"])
            self.assertEqual(result["pe"], 20.5)

if __name__ == '__main__':
    unittest.main()
<<<<<<< HEAD
'''
=======
>>>>>>> 75c3d3ef9af60742bb01863219556b06b61caca5
