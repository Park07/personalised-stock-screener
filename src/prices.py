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
from datetime import datetime, timezone, timedelta
import numpy as np

# alpaca imports
from alpaca.data import CryptoHistoricalDataClient
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.requests import CryptoBarsRequest
# machine learning imports
import pandas as pd
# API keys
from config import ALPACA_SECRET_KEY, ALPACA_PUBLIC_KEY, FMP_API_KEY
# helper functions
from prices_helper import *

from .strategy import (
    bbands_indicator,
    ema_indicator,
    vwap_stock_indicator
)

def get_indicators(tickers, indicators, period, resolution):
    try:
        # strips the json file, creates a list of tickers
        # call alpaca to retrieve market data
        is_crypto = validate_crypto_trading_pairs(tickers)
        start_day = datetime.now(tz=timezone.utc) - timedelta(days=period)

        if is_crypto is True:
            client = CryptoHistoricalDataClient(ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY)
            params = CryptoBarsRequest(symbol_or_symbols=tickers, start=start_day,
                                        timeframe=get_resolution(resolution), limit=10000000)
            res = client.get_crypto_bars(params)

        else:
            client = StockHistoricalDataClient(ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY)
            params = StockBarsRequest(symbol_or_symbols=tickers, start=start_day,
                                        timeframe=get_resolution(resolution), limit=10000000)
            res = client.get_stock_bars(params)

        # unwrap data
        res_iter = iter(res)
        (_, unwrapped_res) = next(res_iter)

        # the return dict
        stock_data = {}
        dfs = {'stock_data': {}, 'timestamp': datetime.now(timezone.utc)}
        for ticker in tickers:
            # stock data
            bars = unwrapped_res[ticker]
            # calc results using talib
            inputs = prepare_inputs(bars)
            # new array of empty bars
            new_bars = []
            for indicator in indicators:
                if indicator in ['BBANDS', 'EMA', 'VWAP']:
                    if indicator == 'BBANDS':
                        bbands_signal = bbands_indicator(
                            ticker,
                            pd.DataFrame(inputs),
                            20,
                            resolution
                        )
                        stock_data[f'{ticker}_BBANDS_signal'] = bbands_signal
                    elif indicator == 'EMA':
                        ema_signal = ema_indicator(
                            ticker,
                            pd.DataFrame(inputs),
                            20,
                            resolution
                        )
                        stock_data[f'{ticker}_EMA_signal'] = ema_signal
                    elif indicator == 'VWAP':
                        vwap_signal = vwap_stock_indicator(
                            ticker,
                            pd.DataFrame(inputs),
                            20,
                            resolution
                        )
                        stock_data[f'{ticker}_VWAP_signal'] = vwap_signal
                else:
                    index = 0
                    calculation_result = talib_calculate_indicators(inputs, indicator)
                    processed_result = process_output(calculation_result)
                    for element in processed_result:
                        # element here should either be a typle of np.ndarray or just a np.float64
                        # tuple case
                        if isinstance(element, tuple):
                            new_element = []
                            for x in element:
                                if np.isnan(x):
                                    new_element = ["null", "null", "null"]
                                else:
                                    new_element.append(float(x))
                            element = new_element
                        # float64 case
                        else:
                            if np.isnan(element):
                                element = "null"
                            else:
                                element = float(element)
                        # the inside of a bar is a 'alpaca.Bar' object, cast it as a dict
                        bar_as_dict = bars[index].__dict__
                        bar_as_dict[indicator] = element
                        new_bars.append(bar_as_dict)
                        index += 1
            stock_data[ticker] = new_bars
            dfs['stock_data'] = stock_data
        return dfs

    except Exception as e:
        logging.error(f"Error: Error processcing params: %s", e)
        return e
