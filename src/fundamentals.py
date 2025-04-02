import requests
from .config import FMP_API_KEY

BASE_URL = "https://financialmodelingprep.com/api/v3/"

def get_valuation(ticker:str) -> dict:
    ratios_quarterly_url = f"{BASE_URL}ratios/{ticker}?period=quarter&apikey={FMP_API_KEY}"
    try:
        response_ratios = requests.get(ratios_quarterly_url)
        response_ratios.raise_for_status()
        ratios_list = response_ratios.json()
        if not ratios_list:
            raise ValueError("No ratio data returned")
        ratios_data = ratios_list[0]
    except Exception as e:
        raise Exception(f"Error fetching ratios data: {e}")
    
    # extracting ratios: PE, peg, pb, PS, EBITDA, PRCICE TO CASH, ENTERPRISE, EARNINGS YIELD
    pe = ratios_data.get("priceEarningsRatio")
    peg = ratios_data.get("priceEarningsToGrowthRatio")
    pb = ratios_data.get("priceToBookRatio")
    ps = ratios_data.get("priceToSalesRatio")
    ev_to_ebitda = ratios_data.get("enterpriseValueMultiple")
    price_to_free_cash_flow = ratios_data.get("priceToFreeCashFlow")
    earnings_yield = 1 / price_to_free_cash_flow if price_to_free_cash_flow and price_to_free_cash_flow != 0 else None

    # Quarterly enterprise API
    ev_url = f"{BASE_URL}enterprise-values/{ticker}?period=quarter&apikey={FMP_API_KEY}"
    try:
        ev_resp = requests.get(ev_url)
        ev_resp.raise_for_status()
        ev_list = ev_resp.json()
        enterprise_value = ev_list[0].get("enterpriseValue") if ev_list else None
    except Exception as e:
        enterprise_value = None  # Optionally log this error

    # If quarterly cash flow data is reliable, add it; otherwise, you can exclude it:
    cf_url = f"{BASE_URL}cash-flow-statement/{ticker}?period=quarter&apikey={FMP_API_KEY}"
    try:
        cf_resp = requests.get(cf_url)
        cf_resp.raise_for_status()
        cf_list = cf_resp.json()
        cf_data = cf_list[0] if cf_list else {}
        free_cash_flow = cf_data.get("freeCashFlow")
        operating_cash_flow = cf_data.get("operatingCashFlow")
    except Exception as e:
        free_cash_flow = None
        operating_cash_flow = None

    return {
        "pe": pe,
        "peg": peg,
        "pb": pb,
        "ps": ps,
        "evToEbitda": ev_ebitda,
        "priceToFreeCashFlow": price_to_free_cash_flow,
        "enterpriseValue": enterprise_value,
        "earningsYield": earnings_yield,
        "freeCashFlowYield": free_cash_flow_yield,
        "freeCashFlow": free_cash_flow,
        "operatingCashFlow": operating_cash_flow
    }
  


