import json
import requests
from config import FMP_API_KEY

# Base URLs for FMP endpoints
BASE_URL = "https://financialmodelingprep.com/api/v3/"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"

# Helper function that fetch from FMP given various URLs (e.g. ratios, key-metrics, ind avg etc)
def fetch_first_item(url: str, error_message: str, default=None) -> dict:
    """   
    Input:
        The URL to fetch data from.
        error message to use if the returned data is empty.
        default (Any): The default value to return in case of error.
    
    Output:
        dict: The first item from the JSON response, or the default value if an error occurs.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(error_message)
        return data[0]
    except Exception as e:
        print(f"Warning: {error_message}: {e}")
        return default
# gets ratios using annual data
def get_ratios(ticker: str) -> dict:
    """    
    Returns:
        dict: The first item of the ratios list.
    """
    url = f"{BASE_URL}ratios/{ticker}?period=annual&apikey={FMP_API_KEY}"
    return fetch_first_item(url, "No ratio data returned")
# key metrics include enterprise value and free Cash
def get_key_metrics(ticker: str) -> dict:
    """    
    Returns:
        dict: The first item of the key metrics list, or an empty dict if none.
    """
    url = f"{BASE_URL}key-metrics/{ticker}?period=annual&apikey={FMP_API_KEY}"
    # Here we want to return an empty dictionary if nothing is available.
    return fetch_first_item(url, "No key metrics data returned", default={})

# Gets future growth idea of the compan
def get_growth(ticker: str) -> dict:
    """    
    Returns:
        dict: The first item of the growth data list, or an empty dict if none.
    """
    url = f"{BASE_URL}financial-growth/{ticker}?period=annual&apikey={FMP_API_KEY}"
    return fetch_first_item(url, "No growth data returned", default={})

# Gets the company profile (ticker, market cap, pe)
def get_profile(ticker: str) -> dict:
    """    
    Returns:
        dict: The company profile data.
    """
    url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
    data = fetch_first_item(url, "No profile data returned")
    if data is None:
        raise ValueError("No profile data returned")
    return data

# gets average industry PE ratio (annual) and have it compared to the company's
def get_industry_pe(industry: str, annual_date: str, exchange: str = "NYSE") -> float:
    """
    Input:
        industry name
        annual_date: The reporting date for the annual data.
        exchange: The stock exchange to filter by .
    
    Returns:
        float: The average industry PE ratio, or None if not found.
    """
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
# Combines all those helper functions together to output them all
def get_valuation(ticker: str) -> dict:
    """
    Input: 
        Company's ticker    
    Return:
        dict: A summary dictionary of essential valuation metrics.
    """
    # Get ratios data and extract reporting period
    ratios_data = get_ratios(ticker)
    reporting_period = ratios_data.get("date") or "2024-12-31"
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
        industry_pe = get_industry_pe(industry, reporting_period)
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
    app.run(host='0.0.0.0', port=5000, debug=True)
