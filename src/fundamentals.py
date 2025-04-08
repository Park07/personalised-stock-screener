import json
import requests
from config import FMP_API_KEY

BASE_URL = "https://financialmodelingprep.com/api/v3/"

# Base URL for v4 endpoints (for aggregated industry data)
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"

def get_valuation(ticker: str) -> dict:
    # Get ratios data
    ratios_annual_url = f"{BASE_URL}ratios/{ticker}?period=annual&apikey={FMP_API_KEY}"
    try:
        response_ratios = requests.get(ratios_annual_url)
        response_ratios.raise_for_status()
        ratios_list = response_ratios.json()
        if not ratios_list:
            raise ValueError("No ratio data returned")
        ratios_data = ratios_list[0]
        reporting_period = ratios_data.get("date")
    except Exception as e:
        raise Exception(f"Error fetching ratios data: {e}")
    
    # Extract ratios
    pe = ratios_data.get("priceEarningsRatio")
    peg = ratios_data.get("priceEarningsToGrowthRatio")
    ps = ratios_data.get("priceToSalesRatio")
    ev_to_ebitda = ratios_data.get("enterpriseValueMultiple")
    roe = ratios_data.get("returnOnEquity")
    debt = ratios_data.get("debtRatio")
    
    # Get key metrics data
    key_metrics_annual_url = f"{BASE_URL}key-metrics/{ticker}?period=annual&apikey={FMP_API_KEY}"
    try:
        response_metrics = requests.get(key_metrics_annual_url)  # Fixed variable name
        response_metrics.raise_for_status()
        metrics_list = response_metrics.json()
        if not metrics_list:
            raise ValueError("No key metrics data returned")
        metrics_data = metrics_list[0]
    except Exception as e:
        metrics_data = {}
        print(f"Warning: Couldn't fetch metrics data: {e}")
    
    enterprise_value = metrics_data.get("enterpriseValueTTM")
    free_cash_flow_yield = metrics_data.get("freeCashFlowYieldTTM")
    
    # Get revenue growth
    growth_url = f"{BASE_URL}financial-growth/{ticker}?period=annual&apikey={FMP_API_KEY}"
    try:
        response_growth = requests.get(growth_url)  
        response_growth.raise_for_status()
        growth_list = response_growth.json()
        if not growth_list:
            raise ValueError("No growth data returned")
        growth_data = growth_list[0]
    except Exception as e:
        growth_data = {}
        print(f"Warning: Couldn't fetch growth data: {e}")
    
    rev_growth = growth_data.get("revenueGrowth")
    eps_growth = growth_data.get("epsgrowth") 

    # get company profile for industry
    profile_url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
    response_profile = requests.get(profile_url)
    response_profile.raise_for_status()
    profile_data = response_profile.json()[0]
    industry = profile_data.get("industry")
    
    # Get industry PE ratio if industry is available
    industry_pe = None
    if industry:
        try:
            industry_pe = get_industry_pe(industry, reporting_period)
        except Exception as e:
            print(f"Couldn't fetch industry PE: {e}")

    
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

def get_industry_pe(industry: str, annual_date, exchange: str = "NYSE") -> float:
    '''
    takes in: industry (str): The industry name to look up.
                exchange (str): The stock exchange to filter by. Default is "NYSE"
    output:   float: The average industry PE ratio.

    '''
    industry_pe_url = f"{BASE_URL_V4}industry_price_earning_ratio?date={annual_date}&exchange={exchange}&apikey={FMP_API_KEY}"

    response = requests.get(industry_pe_url)
    response.raise_for_status()
    industry_list = response.json()
    
    # Search the returned list for the matching industry
    for item in industry_list:
        if item.get("industry") == industry:
            return float(item.get("pe"))
    return None
