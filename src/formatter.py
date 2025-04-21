import logging
import json

def format_comparison_data_for_plotly(db_data_list):
     """Formats data fetched for comparison into Plotly.js parallel coords structure."""
     if not db_data_list: return {"dimensions": [], "tickers": []}

     try:
         dimensions = []
         # Define dimensions based on columns available in the db_data_list dictionaries
         # These should match columns stored by update_chart_data.py
         dim_config = [
             {'label': 'Market Cap ($B)', 'key': 'market_cap', 'divisor': 1e9},
             {'label': 'Current Price ($)', 'key': 'current_price'},
             {'label': 'P/E Ratio', 'key': 'pe_ratio'},
             {'label': 'ROE (%)', 'key': 'roe', 'multiplier': 100},
             {'label': 'Dividend Yield (%)', 'key': 'dividend_yield', 'multiplier': 100},
             {'label': 'Debt/Equity', 'key': 'debt_equity_ratio'},
             {'label': 'Revenue Growth (%)', 'key': 'revenue_growth', 'multiplier': 100},
             {'label': 'Earnings Growth (%)', 'key': 'earnings_growth', 'multiplier': 100},
         ]

         tickers = [company['ticker'] for company in db_data_list]

         for config in dim_config:
             key = config['key']
             values = []
             for company_data in db_data_list:
                 val = company_data.get(key)
                 multiplier = config.get('multiplier', 1)
                 divisor = config.get('divisor', 1)
                 # Apply calculations if value exists
                 processed_val = (val * multiplier / divisor) if val is not None else None
                 values.append(processed_val)

             # Add only if the key actually exists in the fetched data
             if key in db_data_list[0]: # Check first item as sample
                 dimensions.append({'label': config['label'], 'values': values})
             else:
                 logging.warning(f"Metric key '{key}' not found in data for parallel chart formatting.")


         return {"dimensions": dimensions, "tickers": tickers}

     except Exception as e:
         logging.error(f"Error formatting data for Plotly parallel chart: {e}", exc_info=True)
         return {"dimensions": [], "tickers": []}