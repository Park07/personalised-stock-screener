# Gets historical prices from alpaca for analysis

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

# logging
import logging

# webdev stuff
from flask import jsonify
import json

# talib imports
from talib import abstract
from talib.abstract import *
import numpy as np

# alpaca imports
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.models.bars import Bar

# API keys
from config import ALPACA_SECRET_KEY, ALPACA_PUBLIC_KEY, FMP_API_KEY

from datetime import datetime, timezone, timedelta

# machine learning imports
import pandas as pd

# helper functions
from prices_helper import *
# helper to parse in the resolution of the data from the API
def get_resolution(resolution):
    """
    :param resolution: a string either min, hour or day
    :return: returns a alpaca.Timeframe coresponding to the resolution inputted
    """

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

        params = StockBarsRequest(symbol_or_symbols=NDQ100, start=start_day,
                                  timeframe=get_resolution(resolution), limit=10000000)
        res = client.get_stock_bars(params)

        # unwrap data
        res_iter = iter(res)
        (_, unwrapped_res) = next(res_iter)

        # gets all tickers and turns them into json files
        # the return dict
        stock_data = {}
        dfs = {'stock_data': {}, 'timestamp': datetime.now(timezone.utc)}
        for ticker in tickers:
            # stock data
            bars = unwrapped_res[ticker]
            stock_data[ticker] = bars

            # calc results using talib
            # cast bar as a dict
            inputs = prepare_inputs(bars)
            for indicator in indicators:
                talib_res = talib_calculate_indicators(inputs, indicator)
                stock_data[indicator] = talib_res.tolist()

            dfs['stock_data'] = stock_data

        res = json.dumps(dfs, default=str)
        print(res)
        return jsonify(res)

    except Exception as e:
        logging.error(f"Error: fetching NASDAQ 100 tickers: %s", e)
        return

# helper to generate a inputs dictionary
def prepare_inputs(stock_bars):
    """
    takes in a dictionary of stock bars. and formats them for inputting into the TAlib
    abstract function
    
    :param stock bars: a dictionary [{open,high,low,close,volume}]
    :return: dict of ndarrays with the following keyys {open:[],high:[],low:[],close:[],volume:[]}
    """

    try:
        # init everything
        open = np.array([])
        high = np.array([])
        low = np.array([])
        close = np.array([])
        volume = np.array([])

        for bar in stock_bars:
            tmp = bar.__dict__
            # init inputs dict
            open = np.append(open, tmp['open'])
            high = np.append(high, tmp['high'])
            low = np.append(low, tmp['low'])
            close = np.append(close, tmp['close'])
            volume = np.append(volume, tmp['volume'])

        # place into input dict
        inputs = {
            'open': np.array(open),
            'high': np.array(high),
            'low': np.array(low),
            'close': np.array(close),
            'volume': np.array(volume)
        }

        return inputs
    except Exception as e:
        logging.error(f"Error: error processcing inputs for talib: {e}")
        return

# takes in a input dictionary see 'prepare_inputs' turns it into an indicator
def talib_calculate_indicators(inputs, indicator):
    """
    takes in a dictionary of stock bars. and formats them for inputting into the TAlib
    abstract function
    
    :param inputs: stock bars in a dictionary [{open, high, low, close, volume}]
    :param indicator: name of indicator to be calculated by the abstract function
    :return: ndarray of len(inputs)
    """

    try:
        generic_function = abstract.Function(indicator)
        res = generic_function(inputs)
        return res
    except Exception as e:
        logging.error(f"Error: invalid indicators: {e}")
        return
