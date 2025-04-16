import json
import requests
from config import FMP_API_KEY

# Base URLs for FMP endpoints
BASE_URL = "https://financialmodelingprep.com/api/v3/"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"

# helper function to avoid DRY princinple just stashes away common block of code
def fetch_first_item(url: str, error_message: str, default=None) -> dict:
    """
    Input:
        -URL to fetch data from.
        -error message to use if the returned data is empty.
        -default value to return in case of error.
    
    Output:
        dict: The first item from the JSON response, or the default value if an error occurs.
    
    Raises:
        Exception: If no data is returned and default is None.
    """
    try:
        response = requests.get(url)
        # Check for HTTP errors and handle them specifically
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"{response.status_code} {response.reason}")
        data = response.json()
        # Check if data is empty
        if not data:
            raise ValueError("Empty response returned")
        return data[0]
    except requests.exceptions.HTTPError as e:
        print(f"Warning: {error_message}: {e}")
        if default is None:
            raise requests.exceptions.RequestException(f"{error_message}: {e}")
        return default
    except ValueError as e:
        print(f"Warning: {error_message}: {e}")
        if default is None:
            raise requests.exceptions.RequestException(f"{error_message}: {e}")
        return default
    except Exception as e: # pylint: disable=broad-except
        print(f"Warning: {error_message}: {e}")
        if default is None:
            raise requests.exceptions.RequestException(f"{error_message}: {e}") # pylint: disable=broad-except
        return default

def get_ratios(ticker: str) -> dict:
    """
    Returns:
        dict: The first item of the ratios list.
    """
    url = f"{BASE_URL}ratios/{ticker}?period=annual&apikey={FMP_API_KEY}"
    # Use the error message "No ratio data returned" so that empty responses trigger that message.
    return fetch_first_item(url, "Error fetching ratios data")

def get_key_metrics(ticker: str) -> dict:
    """
    Returns:
        dict: The first item of the key metrics list, or an empty dict if none.
    """
    url = f"{BASE_URL}key-metrics/{ticker}?period=annual&apikey={FMP_API_KEY}"
    return fetch_first_item(url, "Error fetching key metrics data", default={})

def get_growth(ticker: str) -> dict:
    """
    Returns:
        dict: The first item of the growth data list, or an empty dict if none.
    """
    url = f"{BASE_URL}financial-growth/{ticker}?period=annual&apikey={FMP_API_KEY}"
    return fetch_first_item(url, "Error fetching growth data", default={})

def get_profile(ticker: str) -> dict:
    """
    Returns:
        dict: The company profile data.
    """
    url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
    data = fetch_first_item(url, "Error fetching profile data")
    if data is None:
        raise ValueError("Error fetching profile data")
    return data

def get_industry_pe(industry: str, annual_date: str, exchange: str = "NYSE") -> float:
    """
    Input:
        industry (str): The industry name to look up.
        annual_date (str): The reporting date for the annual data.
        exchange (str): The stock exchange to filter by.
    
    Returns:
        float: The average industry PE ratio, or None if not found.
    
    Raises:
        requests.HTTPError: If the HTTP request fails.
    """
    # No try/except block here so that HTTP errors propagate.
    industry_pe_url = (
        f"{BASE_URL_V4}industry_price_earning_ratio?date={annual_date}"
        f"&exchange={exchange}&apikey={FMP_API_KEY}"
    )
    response = requests.get(industry_pe_url)
    response.raise_for_status()
    industry_list = response.json()
    for item in industry_list:
        if item.get("industry") == industry:
            return float(item.get("pe"))
    return None

def get_valuation(ticker: str) -> dict:
    """
    Input:
        ticker (str): Company's ticker    
    Returns:
        dict: A summary dictionary of essential valuation metrics.
    """
    # Get ratios data and extract reporting period
    ratios_data = get_ratios(ticker)
    reporting_period = ratios_data.get("date")
    # Extract ratio metrics
    pe = ratios_data.get("priceEarningsRatio")
    peg = ratios_data.get("priceEarningsToGrowthRatio")
    ps = ratios_data.get("priceToSalesRatio")
    ev_to_ebitda = ratios_data.get("enterpriseValueMultiple")
    roe = ratios_data.get("returnOnEquity")
    debt = ratios_data.get("debtRatio")
    # Get key metrics and growth data
    metrics_data = get_key_metrics(ticker)
    enterprise_value = metrics_data.get("enterpriseValue")
    free_cash_flow_yield = metrics_data.get("freeCashFlowYield")
    growth_data = get_growth(ticker)
    rev_growth = growth_data.get("revenueGrowth")
    eps_growth = growth_data.get("epsgrowth")
    # Get company profile to extract industry information
    profile_data = get_profile(ticker)
    industry = profile_data.get("industry")
    industry_pe = None
    if industry:
        try:
            industry_pe = get_industry_pe(industry, reporting_period)
        except Exception as e:
            print(f"Warning: Couldn't fetch industry PE: {e}")
            industry_pe = None

    return {
        "pe": pe,
        "industry_pe": industry_pe,
        "peg": peg,
        "ps": ps,
        "evToEbitda": ev_to_ebitda,
        "roe": roe,
        "debtRatio": debt,
        "enterpriseValue": enterprise_value,
        "freeCashFlowYield": free_cash_flow_yield,
        "revenueGrowth": rev_growth,
        "epsGrowth": eps_growth
    }

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info("Application started")
