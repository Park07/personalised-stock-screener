import json
import requests
from config import FMP_API_KEY

BASE_URL = "https://financialmodelingprep.com/api/v3/"

def get_valuation(ticker:str) -> dict:

    ratios_ttm_url = f"{BASE_URL}ratios-ttm/{ticker}?apikey={FMP_API_KEY}"
    try:
        response_ratios = requests.get(ratios_ttm_url)
        response_ratios.raise_for_status()
        ratios_list = response_ratios.json()
        if not ratios_list:
            raise ValueError("No ratio data returned")
        ratios_data = ratios_list[0]
    except Exception as e:
        raise Exception(f"Error fetching ratios data: {e}")
    
    # extracting ratios: PE, peg, pb, PS, EBITDA, PRCICE TO CASH, ENTERPRISE, EARNINGS YIELD
    pe = ratios_data.get("priceEarningsRatioTTM")
    peg = ratios_data.get("priceEarningsToGrowthRatioTTM")
    pb = ratios_data.get("priceToBookRatioTTM")
    ps = ratios_data.get("priceToSalesRatioTTM")
    ev_to_ebitda = ratios_data.get("enterpriseValueMultipleTTM")
    earnings_yield = 1 / pe if pe and pe != 0 else None

    # key metrics TTM
    key_metrics_ttm_url = f"{BASE_URL}key-metrics-ttm/{ticker}?apikey={FMP_API_KEY}"
    try:
        response_metrics = requests.get(key_metrics_ttm_url)
        response_metrics.raise_for_status()
        metrics_list = response_metrics.json()
        if not metrics_list:
            raise ValueError("No key metrics data returned")
        metrics_data = metrics_list[0]
    except Exception as e:
        metrics_data = {}

    enterprise_value = metrics_data.get("enterpriseValueTTM")
    free_cash_flow_yield = metrics_data.get("freeCashFlowYieldTTM")

    

    return {
        "pe": pe,
        "peg": peg,
        "pb": pb,
        "ps": ps,
        "evToEbitda": ev_to_ebitda,
        "enterpriseValue": enterprise_value,
        "earningsYield": earnings_yield,
        "freeCashFlow_yield": free_cash_flow_yield,
    }
  

# At the end of fundamentals.py
if __name__ == "__main__":
    # Add code to test the function
    import sys
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    else:
        ticker = "AAPL"  # Default ticker for testing
    
    print(f"Getting valuation data for {ticker}...")
    try:
        result = get_valuation(ticker)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
