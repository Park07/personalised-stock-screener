import logging
import json
import pandas as pd

def format_screener_table_data(scored_company_list, top_n=15): # Show top 15 maybe?
    """Formats Top N companies for the screener table display including scores."""
    if not scored_company_list: return []
    display_list = []
    try:
        for item in scored_company_list[:top_n]:
             def fmt_score(score_key):
                 score = item.get(score_key)
                 return f"{score:.1f}" if score is not None and pd.notna(score) else "N/A"
             def fmt_mkt_cap(mc_key):
                 mc_val = item.get(mc_key)
                 return f"${mc_val / 1e9:.1f}B" if mc_val is not None and pd.notna(mc_val) else 'N/A'

             display_item = {
                 'ticker': item.get('ticker'),
                 'name': item.get('company_name') or item.get('name', 'N/A'),
                 'sector': item.get('sector', 'N/A'),
                 'market_cap': fmt_mkt_cap('market_cap'),
                 'overall_score': fmt_score('overall_score'),
                 'valuation_score': fmt_score('valuation_score'),
                 'health_score': fmt_score('health_score'),
                 'growth_score': fmt_score('growth_score'),
                 # 'current_price': item.get('current_price')
             }
             display_list.append(display_item)
        return display_list
    except Exception as e:
         logging.exception(f"Error formatting screener list")
         return []