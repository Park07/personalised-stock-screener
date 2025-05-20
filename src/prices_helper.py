# Helper functions to retrieve historical data

import json
import logging
from urllib.request import urlopen
import numpy as np
# from talib import abstract
from alpaca.data.timeframe import TimeFrame

# stock_client = StockHistoricalDataClient("api-key",  "secret-key")

# cached_data = {}

# helper to parse in the resolution of the data from the API


def get_resolution(resolution):
    """
    :param resolution: a string either min, hour or day
    :return: returns a alpaca.Timeframe coresponding to the resolution inputted
    """

    if resolution == "min":
        return TimeFrame.Minute
    if resolution == "hour":
        return TimeFrame.Hour
    if resolution == "day":
        return TimeFrame.Day

    # defaults to minute
    return TimeFrame.Minute

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
        logging.error(f"Error: invalid indicators: %s", e)
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
            if not isinstance(bar, dict):
                tmp = bar.__dict__
            else:
                tmp = bar
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
        logging.error(f"Error: error processcing inputs for talib: %s", e)
        return

# Helper to grab the current avaliable trading pairs on alpaca


def validate_crypto_trading_pairs(cryptos):
    valid_pairs = [
        'AAVE/USD',
        'BCH/USD',
        'BTC/USD',
        'DOGE/USD',
        'ETH/USD',
        'LINK/USD',
        'LTC/USD',
        'SUSHI/USD',
        'UNI/USD',
        'YFI/USD']
    for crypto in cryptos:
        if crypto not in valid_pairs:
            return False

    return True

# helper function to process outputs from talib


def process_output(output):
    # if the calculation result is a 1d array do nothing
    # else zip it up into a 1d array
    # returns either a list of tuples or a list of np.float64s
    """
    :param output: a numpy array which
    :return: either returns a np.ndarray nothing changed,
    or a ndarray of tuples with the same len as the output
    """
    try:
        if isinstance(output, np.ndarray) and output.ndim == 1:
            return output
        return list(zip(*output))
    except Exception as _:
        return output


# Helper to grab json data from a URL
def get_jsonparsed_data(url):
    """
    Parses the JSON response from the provided URL.

    :param url: The API endpoint to retrieve data from.
    :return: Parsed JSON data as a dictionary.
    """
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)

# Helper to retrieve nasdaq 100 tickers from the FMP API


def get_nasdaq_tickers(FMP_API_KEY):
    """
    Gets the SNP100 tickers from the FMP API.

    :param url: API key for FMP
    :return: array of instrument names
    """

    try:
        api_url = (
            f"https://financialmodelingprep.com/api/v3/nasdaq_constituent?"
            f"apikey={FMP_API_KEY}"
        )
        data = get_jsonparsed_data(api_url)
        logging.info("Success: retrieved NASDAQ 100 tickers.")

        return data
    except Exception as e:
        logging.error(f"Error: fetching NASDAQ 100 tickers: %s", e)
        return
