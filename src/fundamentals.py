import json
import requests
from config import FMP_API_KEY

BASE_URL = "https://financialmodelingprep.com/api/v3/"

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
    except Exception as e:
        raise Exception(f"Error fetching ratios data: {e}")
    
    # Extract ratios
    pe = ratios_data.get("priceEarningsRatioTTM")
    peg = ratios_data.get("priceEarningsToGrowthRatioTTM")
    ps = ratios_data.get("priceToSalesRatioTTM")
    ev_to_ebitda = ratios_data.get("enterpriseValueMultipleTTM")
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
    
    return {
        "pe": pe,
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