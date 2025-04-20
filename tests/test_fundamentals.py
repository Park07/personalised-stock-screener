import unittest
from unittest.mock import patch, MagicMock
from src.fundamentals import (
    get_ratios,
    get_key_metrics,
    get_growth,
    get_profile,
    get_key_metrics_summary
)


class TestGetKeyMetricsSummary(unittest.TestCase):
    # ---------------------------- SUCCESS PATHS ----------------------------
    @patch('src.fundamentals.get_ratios')
    @patch('src.fundamentals.get_key_metrics')
    @patch('src.fundamentals.get_growth')
    @patch('src.fundamentals.get_profile')
    @patch('src.fundamentals.yahoo_sector_pe')
    def test_get_key_metrics_summary_all_ttm_fields(
        self,
        mock_sector_pe, mock_profile, mock_growth,
        mock_key_metrics, mock_ratios
    ):
        """Test when all TTM fields are available"""
        # Mock return values
        mock_ratios.return_value = {
            "peRatioTTM": 20.5,
            "pegRatioTTM": 1.5,
            "priceToSalesRatioTTM": 3.2,
            "returnOnEquityTTM": 0.15,
            "debtRatioTTM": 0.35
        }
        mock_key_metrics.return_value = {
            "enterpriseValueTTM": 1_000_000_000,
            "freeCashFlowYieldTTM": 0.05
        }
        mock_growth.return_value = {
            "revenueGrowth": 0.12,
            "epsGrowth": 0.08
        }
        mock_profile.return_value = {
            "sector": "Technology"
        }
        # Hardcode sector PE
        mock_sector_pe.return_value = 22.3

        # Call the function
        result = get_key_metrics_summary("AAPL")

        # Assertions
        self.assertEqual(result["pe"], 20.5)
        self.assertEqual(result["sector_pe"], 22.3)
        self.assertEqual(result["peg"], 1.5)
        self.assertEqual(result["ps"], 3.2)
        self.assertEqual(result["roe"], 0.15)
        self.assertEqual(result["debtRatio"], 0.35)
        self.assertEqual(result["enterpriseValue"], 1_000_000_000)
        self.assertEqual(result["freeCashFlowYield"], 0.05)
        self.assertEqual(result["revenueGrowth"], 0.12)
        self.assertEqual(result["epsGrowth"], 0.08)

    @patch('src.fundamentals.get_ratios')
    @patch('src.fundamentals.get_key_metrics')
    @patch('src.fundamentals.get_growth')
    @patch('src.fundamentals.get_profile')
    @patch('src.fundamentals.yahoo_sector_pe')
    def test_get_key_metrics_summary_fallback_to_annual(
        self,
        mock_sector_pe, mock_profile, mock_growth,
        mock_key_metrics, mock_ratios
    ):
        """Test fallback to annual fields when TTM not available"""
        # Mock return values with annual fields instead of TTM
        mock_ratios.return_value = {
            "priceEarningsRatio": 21.5,
            "priceEarningsToGrowthRatio": 1.6,
            "priceToSalesRatio": 3.3,
            "returnOnEquity": 0.16,
            "debtRatio": 0.36
        }
        mock_key_metrics.return_value = {
            "enterpriseValue": 1_100_000_000,
            "freeCashFlowYield": 0.06
        }
        mock_growth.return_value = {
            "revenueGrowth": 0.13,
            "epsGrowth": 0.09
        }
        mock_profile.return_value = {
            "sector": "Technology"
        }
        # Hardcode sector PE
        mock_sector_pe.return_value = 23.4

        # Call the function
        result = get_key_metrics_summary("MSFT")

        # Assertions
        self.assertEqual(result["pe"], 21.5)
        self.assertEqual(result["sector_pe"], 23.4)
        self.assertEqual(result["peg"], 1.6)
        self.assertEqual(result["ps"], 3.3)
        self.assertEqual(result["roe"], 0.16)
        self.assertEqual(result["debtRatio"], 0.36)
        self.assertEqual(result["enterpriseValue"], 1_100_000_000)
        self.assertEqual(result["freeCashFlowYield"], 0.06)
        self.assertEqual(result["revenueGrowth"], 0.13)
        self.assertEqual(result["epsGrowth"], 0.09)


if __name__ == '__main__':
    unittest.main()
