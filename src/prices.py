# Gets historical prices from alpaca for analysis

# %%
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
from datetime import datetime, timezone, timedelta, date
import numpy as np

# alpaca imports
from alpaca.data import CryptoHistoricalDataClient
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.models.bars import Bar
# API keys
from config import ALPACA_SECRET_KEY, ALPACA_PUBLIC_KEY, FMP_API_KEY
# helper functions
from prices_helper import *

# usage
# params bars: List<Bar> min, hour, day
# agg_numer: int
# e.g. 5 minunte


def agg_bars(stock_data, agg_number):
    # helper func takes a bar array and dict key
    # sends all of that dict's keys values into a array
    def key_to_array(tmp_bars, key):
        values = []
        for bar in tmp_bars:
            values.append(float(bar[key]))
        return values

    if agg_number <= 1:
        return stock_data

    stock_data_dict = {}
    companies = stock_data.keys()
    for company_name in companies:
        bars = stock_data[company_name]

        tmp_bar_arr = []
        agged_bars = []
        for bar in bars:
            bar = bar.__dict__
            tmp_bar_arr.append(bar)

            if len(tmp_bar_arr) == agg_number:
                highs = key_to_array(tmp_bar_arr, "high")
                lows = key_to_array(tmp_bar_arr, "low")
                volumes = key_to_array(tmp_bar_arr, "volume")
                trade_counts = key_to_array(tmp_bar_arr, "trade_count")

                agged_bar = {
                    "symbol": tmp_bar_arr[0]["symbol"],
                    "timestamp": tmp_bar_arr[-1]["timestamp"],
                    "open": tmp_bar_arr[0]["open"],
                    "high": max(highs),
                    "low": min(lows),
                    "close": tmp_bar_arr[-1]["close"],
                    "volume": sum(volumes),
                    "trade_count": sum(trade_counts),
                    "vwap": tmp_bar_arr[-1]["vwap"]
                }

                agged_bars.append(agged_bar)
                tmp_bar_arr = []
            # aggregation done
        stock_data_dict[company_name] = agged_bars
    return stock_data_dict


def get_prices(tickers, resolution, **kwargs):
    # optional: make sure that the end day is after the start day
    # makes end day from iso format
    # E.G. date.fromisoformat('YYYY-MM-DD')
    end_date = kwargs.get('end_date', None)
    start_date = kwargs.get('start_date', None)
    # period from now is an easier way of handeling the dates
    # choose how many days back you want to fetch prices
    period = kwargs.get('days_from_now', None)
    try:
        if end_date is not None and start_date is not None:
            end_date = date.fromisoformat(str(end_date))
            print(type(end_date))
        else:
            start_day = datetime.now(tz=timezone.utc) - timedelta(days=period)
        is_crypto = validate_crypto_trading_pairs(tickers)

        # crypto data
        if is_crypto is True:
            client = CryptoHistoricalDataClient(
                ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY)
            # start and end dates
            if end_date is not None and start_date is not None:
                params = CryptoBarsRequest(
                    symbol_or_symbols=tickers,
                    start=start_date,
                    end=end_date,
                    timeframe=get_resolution(resolution),
                    limit=10000000)
            # time period from NOW till a certain number of days in the past
            else:
                params = CryptoBarsRequest(
                    symbol_or_symbols=tickers,
                    start=start_day,
                    timeframe=get_resolution(resolution),
                    limit=10000000)
            res = client.get_crypto_bars(params)
        # stocks data
        else:
            client = StockHistoricalDataClient(
                ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY)
            # start and end dates
            if end_date is not None and start_date is not None:
                params = StockBarsRequest(
                    symbol_or_symbols=tickers,
                    start=start_date,
                    end=end_date,
                    timeframe=get_resolution(resolution),
                    limit=10000000)
            # time period from NOW till a certain number of days in the past
            else:
                params = StockBarsRequest(
                    symbol_or_symbols=tickers,
                    start=start_day,
                    timeframe=get_resolution(resolution),
                    limit=10000000)
            res = client.get_stock_bars(params)
        # unwrap data
        res_iter = iter(res)
        (_, unwrapped_res) = next(res_iter)
        return unwrapped_res
    except Exception as e:
        logging.error(f"Error: Error processcing params: %s", e)
        return e


def get_indicators(tickers, indicators, period, resolution, **kwargs):
    try:
        # strips the json file, creates a list of tickers
        # call alpaca to retrieve market data
        agg_number = kwargs.get('agg_number', None)
        is_crypto = validate_crypto_trading_pairs(tickers)
        start_day = datetime.now(tz=timezone.utc) - timedelta(days=period)

        if is_crypto is True:
            client = CryptoHistoricalDataClient(
                ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY)
            params = CryptoBarsRequest(
                symbol_or_symbols=tickers,
                start=start_day,
                timeframe=get_resolution(resolution),
                limit=10000000)
            res = client.get_crypto_bars(params)

        else:
            client = StockHistoricalDataClient(
                ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY)
            params = StockBarsRequest(
                symbol_or_symbols=tickers,
                start=start_day,
                timeframe=get_resolution(resolution),
                limit=10000000)
            res = client.get_stock_bars(params)

        # unwrap data
        res_iter = iter(res)
        (_, unwrapped_res) = next(res_iter)
        if agg_number is not None:
            unwrapped_res = agg_bars(unwrapped_res, agg_number)
        # the return dict
        stock_data = {}
        dfs = {'stock_data': {}, 'timestamp': datetime.now(timezone.utc)}
        for ticker in tickers:
            # stock data
            bars = unwrapped_res[ticker]
            inputs = prepare_inputs(bars)
            if not isinstance(bars[0], dict):
                bars = [bar.__dict__.copy() for bar in bars]
            # calc results using talib
            # new array of empty bars
            for indicator in indicators:
                calculation_result = talib_calculate_indicators(
                    inputs, indicator)
                processed_result = process_output(calculation_result)
                for i, element in enumerate(processed_result):
                    if isinstance(element, tuple):
                        new_element = []
                        for x in element:
                            if np.isnan(x):
                                new_element.append(float(x))
                            else:
                                new_element.append("null")
                        element = new_element
                    else:
                        if np.isnan(element):
                            element = "null"
                        else:
                            element = float(element)
                    bars[i][indicator] = element
                stock_data[ticker] = bars
            dfs['stock_data'] = stock_data
        return dfs

    except Exception as e:
        logging.error(f"Error: Error processcing params: %s", e)
        return e

# %%
