# calculate_dcf endpoint works, backend logic tested and passes
# only putitng these values cos free limit tier restricts more than 6 requests
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

SECTORS = { 
    "Technology": [
        'AAPL', 'MSFT', 'GOOG', 'NVDA', 'ADBE', 'CRM', 'AMD', 'PYPL',
        'INTC', 'CSCO', 'TXN', 'QCOM', 'IBM', 'ORCL', 'ACN', 'SNPS', 'CDNS'
    ],
    "Consumer Cyclical": [
        'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TGT',
        'BKNG', 'GM', 'CMG', 'TJX', 'ROST', 'MAR', 'YUM'
    ],
    "HealthCare": [
        'JNJ', 'UNH', 'PFE', 'MRK', 'ABBV', 'TMO', 'ABT', 'LLY',
        'DHR', 'MDT', 'AMGN', 'ISRG', 'GILD', 'BMY', 'SYK', 'ZBH', 'VRTX'
    ],
    "Financial Services": [
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'C', 'AXP',
        'USB', 'COF', 'MET', 'AIG', 'BK', 'PNC', 'TROW', 'MMC'
    ],
    "Communication Services": [ 
        'GOOG', 'META', 'DIS', 'NFLX', 'CMCSA', 'VZ', 'T', 'TMUS',
        'CHTR', 'WBD', 'FOXA', 'PARA',
    ],
     "Industrials": [ 
        'CAT', 'UNP', 'HON', 'UPS', 'LMT', 'BA', 'DE', 'GE',
        'FDX', 'GD', 'RTX', 'EMR', 'ETN', 'ITW', 'WM', 'JCI', 
    ],
    "Consumer Staples": [ 
        'PG', 'KO', 'PEP', 'WMT', 'COST', 'MO', 'MDLZ', 'CL',
        'PM', 'GIS', 'KMB', 'EL', 'ADM', 'KDP', 'KR' 
    ],
    "Energy": [ 
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'WMB', 'KMI'
     ],
    "Utilities": [ 
        'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'SRE', 'PEG', 'XEL', 'ED', 'D'
    ],
    "Real Estate": [ 
        'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'WELL', 'AVB', 'EQR', 'O'
     ],
    "Materials": [ 
        'LIN', 'APD', 'SHW', 'ECL', 'NUE', 'DD', 'PPG', 'DOW', 'FCX', 'ALB'
     ]
}

STOCK_UNIVERSE = list(set(
    ticker for sector_tickers in SECTORS.values() for ticker in sector_tickers
))