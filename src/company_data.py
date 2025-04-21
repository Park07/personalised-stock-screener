FAIR_VALUE_DATA = {
    'AAPL': {"fair_value": 141.52864356152915, "valuation_status": "Overvalued"},
    'NVDA': {"fair_value": 43.90598087684451, "valuation_status": "Overvalued"},
    'MSFT': {"fair_value": 250.68220502329478, "valuation_status": "Overvalued"},
    'TSLA': {"fair_value": 17.777165048414727, "valuation_status": "Overvalued"},
    'GOOG': {"fair_value": 134.10404691958382, "valuation_status": "Overvalued"},
    'SBUX': {"fair_value": 60.032336163203325, "valuation_status": "Overvalued"},
    'AMZN': {"fair_value": 35.99025837057056, "valuation_status": "Overvalued"},
    'JPM': {"fair_value": 85.73865380104637, "valuation_status": "Overvalued"},
    'ADBE': {"fair_value": 306.1240311714045, "valuation_status": "Overvalued"},
    'CRM': {"fair_value": 289.5487901230884, "valuation_status": "Undervalued"},
    'AMD': {"fair_value": 28.78959059764345, "valuation_status": "Overvalued"},
    'PYPL': {"fair_value": 98.2473820072602, "valuation_status": "Undervalued"},
    'PG': {"fair_value": 254.69772167989305, "valuation_status": "Undervalued"},
    'KO': {"fair_value": 29.8456918830064, "valuation_status": "Overvalued"},
    'PEP': {"fair_value": 152.44151778169382, "valuation_status": "Undervalued"},
    'WMT': {"fair_value": 136.06271619208434, "valuation_status": "Undervalued"},
    'COST': {"fair_value": 295.06816387800217, "valuation_status": "Overvalued"},
    'PM': {"fair_value": 215.77643061457027, "valuation_status": "Undervalued"},
    'HD': {"fair_value": 236.2232262019357, "valuation_status": "Overvalued"},
    'ABBV': {"fair_value": 275.87380950821534, "valuation_status": "Undervalued"},
    'TXN': {"fair_value": 28.358290461732132, "valuation_status": "Overvalued"},
    'CVX': {"fair_value": 247.71643477084137, "valuation_status": "Undervalued"},
}

# Tickers grouped by sectors for filtering
SECTORS = {
    "Technology": ['AAPL', 'MSFT', 'GOOG', 'NVDA', 'ADBE', 'CRM', 'AMD', 'PYPL', 'AMZN', 'TSLA', 'TXN'],
    "Consumer": ['SBUX', 'PG', 'KO', 'PEP', 'WMT', 'COST', 'HD'],
    "Financial": ['JPM'],
    "Healthcare": ['ABBV'],
    "Energy": ['CVX'],
    "Other": ['PM']
}

STOCK_UNIVERSE = list(FAIR_VALUE_DATA.keys())
