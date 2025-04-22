import logging
import json
import pandas as pd

def format_ranked_list_for_display(ranked_list, top_n=15):
    """Formats Top N ranked companies including key metrics and summary."""
    if not ranked_list: return []
    try:
        display_list = []
        for item in ranked_list[:top_n]:
             # Helper to safely format numbers
             def format_num(val, decimals=1, scale=1, suffix=''):
                 if val is None or pd.isna(val): return 'N/A'
                 try: return f"{round(float(val) * scale, decimals)}{suffix}"
                 except (ValueError, TypeError): return 'N/A'

             display_item = {
                 'ticker': item.get('ticker'),
                 'name': item.get('company_name') or item.get('name', 'N/A'),
                 'sector': item.get('sector', 'N/A'),
                 'market_cap': format_num(item.get('market_cap'), 1, 1e-9, 'B'), 
                 'pe_ratio': format_num(item.get('pe_ratio'), 1),
                 'roe': format_num(item.get('roe'), 1, 100, '%'), 
                 'profile_score': format_num(item.get('profile_score'), 1), 
                 'recommendation': item.get('recommendation_summary', 'N/A')
             }
             display_list.append(display_item)
        return display_list
    except Exception as e:
         logging.exception(f"Error formatting ranked list") # Log full traceback
         return []

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