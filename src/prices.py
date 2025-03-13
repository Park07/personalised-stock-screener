# Gets historical prices from alpaca for analysis

from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.models.bars import Bar

from config import ALPACA_SECRET_KEY, ALPACA_PUBLIC_KEY, FMP_API_KEY
from urllib.request import urlopen
from datetime import datetime, timezone, timedelta

import talib as ta
import numpy as np
import pandas as pd
import logging
from flask import jsonify
import json

# helper functions
from prices_helper import *

# returns a json response object (dict) with nasdaq 100 tickers
# data format:
# "symbol": "AAPL",
# "name": "Apple Inc.",
# "sector": "Technology",
# "subSector": "Technology",
# "headQuarter": "Cupertino, CA",
# "dateFirstAdded": null,
# "cik": "0000320193",
# "founded": "1976-04-01"

def get_resolution(resolution):
    if resolution == "min":
        return TimeFrame.Minute
    elif resolution == "hour":
        return TimeFrame.Hour
    elif resolution == "day":
        return TimeFrame.Day
    else:
        # defaults to minute
        return TimeFrame.Minute

def get_indicators(tickers, indicators, period, resolution):
    try:
        # strips the json file, creates a list of tickers
        data = get_nasdaq_tickers(FMP_API_KEY)
        NDQ100 = []
        for element in data:
            NDQ100.append(element["symbol"])
        
        # call alpaca to retrieve market data
        client = StockHistoricalDataClient(ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY)
        start_day = datetime.now(tz=timezone.utc) - timedelta(days=period)

        params = StockBarsRequest(symbol_or_symbols=NDQ100, start=start_day, timeframe=get_resolution(resolution), limit=10000000)
        res = client.get_stock_bars(params)

        # unwrap data
        res_iter = iter(res)
        (_, unwrapped_res) = next(res_iter)

        # gets all tickers and turns them into json files
        dfs = {}
        for ticker in tickers:
            bars = unwrapped_res[ticker]
            dfs[ticker] = bars
        
        res = json.dumps(dfs)
        return jsonify(res)
        
    except Exception as e:
        logging.error(f"Error: fetching NASDAQ 100 tickers: {e}")
        return



# def main():
#     try:
#         data = get_nasdaq_tickers(FMP_API_KEY)
        
#         # strips the json file, creates a list of tickers
#         NDQ100 = []
#         for element in data:
#             NDQ100.append(element["symbol"])

#         # call alpaca to retrieve market data
#         client = StockHistoricalDataClient(ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY)
#         start_day = datetime.now(tz=timezone.utc) - timedelta(days=3)
#         # end_day = datetime.now(tz=timezone.utc)
#         params = StockBarsRequest(symbol_or_symbols=NDQ100, start=start_day, timeframe=TimeFrame.Minute, limit=10000000)
#         res = client.get_stock_bars(params)

#         # unwrap data
#         res_iter = iter(res)
#         (_, unwrapped_res) = next(res_iter)

#         # gets all tickers and turns them into dataframes
#         dfs = {}
#         for ticker in NDQ100:
#             bars = unwrapped_res[ticker]
#             df = pd.DataFrame([bar.__dict__ for bar in bars])
#             dfs[ticker] = df
        
#     except Exception as e:
#         logging.error(f"Error: fetching NASDAQ 100 tickers: {e}")
#         return

