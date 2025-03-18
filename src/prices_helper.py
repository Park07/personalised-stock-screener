# Helper functions to retrieve historical data

import json
import logging
from urllib.request import urlopen
from alpaca.data import StockHistoricalDataClient

stock_client = StockHistoricalDataClient("api-key",  "secret-key")

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
        api_url=f"https://financialmodelingprep.com/api/v3/nasdaq_constituent?apikey={FMP_API_KEY}"
        data = get_jsonparsed_data(api_url)
        logging.info("Success: retrieved NASDAQ 100 tickers.")

        return data
    except Exception as e:
        logging.error(f"Error: fetching NASDAQ 100 tickers: %s", e)
        return
