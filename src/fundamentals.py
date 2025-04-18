import json
import requests
import logging
from tabulate import tabulate
from colorama import Fore, Style, init
from config import FMP_API_KEY
from functools import lru_cache
import yfinance as yf
import pandas as pd


BASE_URL = "https://financialmodelingprep.com/api/v3/"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"
WIKI_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# Enhanced API calling functions with debugging and fallbacks

def fetch_data_with_fallback(ticker, endpoint_types, error_message):
    """
<<<<<<< HEAD
    Input:
        -URL to fetch data from.
        -error message to use if the returned data is empty.
        -default value to return in case of error.

    Output:
        dict: The first item from the JSON response, or the default value if an error occurs.

    Raises:
        Exception: If no data is returned and default is None.
=======
    Try multiple endpoint types and return the first successful result.

    Args:
        ticker: The stock ticker symbol
        endpoint_types: List of tuples (endpoint, is_ttm) to try in order
        error_message: Error message to display if all endpoints fail

    Returns:
        The first successful API response or default {}
>>>>>>> 013cdb6297db0edac055ede28801704b6280a701
    """
    for endpoint, is_ttm in endpoint_types:
        try:
            # Build URL based on whether this is a TTM endpoint or not
            if is_ttm:
                url = f"{BASE_URL}{endpoint}-ttm/{ticker}?apikey={FMP_API_KEY}"
            else:
                url = f"{BASE_URL}{endpoint}/{ticker}?period=annual&apikey={FMP_API_KEY}"

            print(f"DEBUG: Trying endpoint: {url}")
            response = requests.get(url)
            print(f"DEBUG: Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    print(f"DEBUG: Successfully got data from {endpoint}" + ("-ttm" if is_ttm else ""))
                    return data[0]
                else:
                    print(f"DEBUG: Empty data from {endpoint}" + ("-ttm" if is_ttm else ""))
        except Exception as e:
            print(f"DEBUG: Error with {endpoint}" + ("-ttm" if is_ttm else "") + f": {e}")

    # If we get here, all endpoints failed
    print(f"WARNING: {error_message}: All endpoints failed")
    return {}

def get_ratios(ticker):
    """Get financial ratios with fallback from TTM to annual"""
    endpoint_types = [
        ("ratios", True),   # Try TTM first
        ("ratios", False)   # Fall back to annual
    ]
    return fetch_data_with_fallback(ticker, endpoint_types, "Error fetching ratios data")

def get_key_metrics(ticker):
    """Get key metrics with fallback from TTM to annual"""
    endpoint_types = [
        ("key-metrics", True),   # Try TTM first
        ("key-metrics", False)   # Fall back to annual
    ]
    return fetch_data_with_fallback(ticker, endpoint_types, "Error fetching key metrics data")

def get_growth(ticker):
    """Get financial growth data"""
    endpoint_types = [
        ("financial-growth", False)  # Only annual makes sense for growth
    ]
    return fetch_data_with_fallback(ticker, endpoint_types, "Error fetching growth data")

def get_profile(ticker):
    """Get company profile"""
    try:
        url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
        print(f"DEBUG: Fetching profile from {url}")
        response = requests.get(url)
        print(f"DEBUG: Profile response status: {response.status_code}")

        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"{response.status_code} {response.reason}")

        data = response.json()
        if not data:
            raise ValueError("Empty response returned for profile")

        return data[0]
    except Exception as e:
        print(f"WARNING: Error fetching profile data: {e}")
        return {}

def map_sector_name(fmp_sector):
    """
<<<<<<< HEAD
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
=======
    Maps sector names from FMP API to standard S&P 500 sector names.

    Args:
        fmp_sector: Sector name from FMP API

    Returns:
        Mapped sector name that matches S&P 500 classifications
>>>>>>> 013cdb6297db0edac055ede28801704b6280a701
    """
    if not fmp_sector:
        return None

    # Standard S&P 500 sectors
    sp500_sectors = [
        "Information Technology",
        "Health Care",
        "Consumer Discretionary",
        "Consumer Staples",
        "Financials",
        "Industrials",
        "Materials",
        "Real Estate",
        "Communication Services",
        "Energy",
        "Utilities"
    ]

    # Direct mapping for common FMP API sector names
    sector_mapping = {
        "Technology": "Information Technology",
        "Healthcare": "Health Care",
        "Consumer Services": "Consumer Discretionary",
        "Consumer Goods": "Consumer Staples",
        "Basic Materials": "Materials",
        "Financial Services": "Financials",
        "Financial": "Financials",
        "Industrial Goods": "Industrials",
        "Conglomerates": "Industrials"
    }

    # If sector is already in standard format, return as is
    if fmp_sector in sp500_sectors:
        return fmp_sector

    # Try to map to standard format
    mapped_sector = sector_mapping.get(fmp_sector)
    print(f"DEBUG: Mapping sector '{fmp_sector}' -> '{mapped_sector or 'NOT FOUND'}'")

    return mapped_sector or fmp_sector

def get_valuation(ticker: str) -> dict:
    """
<<<<<<< HEAD
    Input:
        ticker (str): Company's ticker
=======
    Get company valuation with flexible field names and fallbacks.

    Args:
        ticker: The stock ticker symbol

>>>>>>> 013cdb6297db0edac055ede28801704b6280a701
    Returns:
        Dictionary of valuation metrics
    """
    print(f"\nDEBUG: Starting valuation fetch for {ticker}")

    # Get ratios data - try both TTM and annual
    ratios_data = get_ratios(ticker)
    print(f"DEBUG: Ratios data keys: {list(ratios_data.keys())[:5]}...")

    # Try different field name conventions
    pe = ratios_data.get("peRatioTTM") or ratios_data.get("priceEarningsRatio")
    peg = ratios_data.get("pegRatioTTM") or ratios_data.get("priceEarningsToGrowthRatio")
    ps = ratios_data.get("priceToSalesRatioTTM") or ratios_data.get("priceToSalesRatio")
    roe = ratios_data.get("returnOnEquityTTM") or ratios_data.get("returnOnEquity")
    debt = ratios_data.get("debtRatioTTM") or ratios_data.get("debtRatio")

    print(f"DEBUG: Extracted PE={pe}, PEG={peg}, PS={ps}, ROE={roe}, Debt={debt}")

    # Get key metrics data - try both TTM and annual
    metrics_data = get_key_metrics(ticker)
    print(f"DEBUG: Metrics data keys: {list(metrics_data.keys())[:5]}...")

    enterprise_value = metrics_data.get("enterpriseValueTTM") or metrics_data.get("enterpriseValue")
    free_cash_flow_yield = metrics_data.get("freeCashFlowYieldTTM") or metrics_data.get("freeCashFlowYield")

    print(f"DEBUG: Extracted EV={enterprise_value}, FCF Yield={free_cash_flow_yield}")

    # Get growth data (annual only)
    growth_data = get_growth(ticker)
    print(f"DEBUG: Growth data keys: {list(growth_data.keys())[:5]}...")

    rev_growth = growth_data.get("revenueGrowth")
    eps_growth = growth_data.get("epsgrowth") or growth_data.get("epsGrowth")

    print(f"DEBUG: Extracted Rev Growth={rev_growth}, EPS Growth={eps_growth}")

    # Get company profile for sector information
    profile_data = get_profile(ticker)
    fmp_sector = profile_data.get("sector")
    sector = map_sector_name(fmp_sector)

    # Get sector PE
    sector_pe = None
    if sector:
        try:
            print(f"DEBUG: Attempting to get sector PE for {sector}")
            sector_pe = yahoo_sector_pe(sector)
            print(f"DEBUG: Sector PE: {sector_pe}")
        except Exception as e:
            print(f"WARNING: Couldn't fetch sector PE: {e}")

    # Build result dictionary
    result_dict = {
        "pe": pe,
        "sector_pe": sector_pe,
        "peg": peg,
        "ps": ps,
        "roe": roe,
        "debtRatio": debt,
        "enterpriseValue": enterprise_value,
        "freeCashFlowYield": free_cash_flow_yield,
        "revenueGrowth": rev_growth,
        "epsGrowth": eps_growth
    }

    print(f"DEBUG: Final result: {result_dict}")
    return result_dict

@lru_cache(maxsize=1)
def _sp500_companies() -> pd.DataFrame:
    # Fetch S&P 500 companies data from Wikipedia with improved column handling.

    tables = pd.read_html(WIKI_SP500_URL, flavor="bs4")

    # Debug: Print all available columns to identify the correct one
    first_table = tables[0]
    print(f"DEBUG: Available columns in Wikipedia S&P 500 table: {list(first_table.columns)}")

    # Look for GICS Sector column with different possible formats
    gics_col = None
    for col in first_table.columns:
        if 'GICS' in str(col) and 'Sector' in str(col):
            gics_col = col
            print(f"DEBUG: Found GICS Sector column: '{gics_col}'")
            break

    if not gics_col:
        # Fallback: Just use the column at index 1 (typically sector in S&P 500 table)
        gics_col = first_table.columns[1]
        print(f"DEBUG: Falling back to column at index 1: '{gics_col}'")

    # Create DataFrame with normalized column names
    df = tables[0][["Symbol", gics_col]]
    df.columns = ["ticker", "sector"]

    # Normalize sector names by stripping whitespace
    df["sector"] = df["sector"].str.strip()

    # Debug: Print unique sectors found
    unique_sectors = df["sector"].unique()
    print(f"DEBUG: Unique sectors found: {unique_sectors}")

    return df

def yahoo_sector_pe(sector: str) -> float | None:
    # Market‑cap‑weighted trailing‑12‑month P/E for all S&P‑500 stocks in `sector`.
    df = _sp500_companies()
    tickers = df.loc[df["sector"] == sector, "ticker"].tolist()
    if not tickers:
        raise ValueError(f"No S&P‑500 tickers found for sector '{sector}'")

    records = []
    for tkr in tickers:
        info = yf.Ticker(tkr).info
        mc   = info.get("marketCap")
        eps  = info.get("trailingEps")
        sh   = info.get("sharesOutstanding")
        if mc and eps and sh and eps != 0:
            net_income = eps * sh          # EPS * shares = trailing NI
            records.append({"mc": mc, "ni": net_income})

    if not records:
        return None

    sector_mc = sum(r["mc"] for r in records)
    sector_ni = sum(r["ni"] for r in records)
    return sector_mc / sector_ni if sector_ni else None


# NEW: fetch sector P/E instead of sector P/E
def get_sector_pe(sector, annual_date, exchange="NYSE"):
    url = (
        f"{BASE_URL_V4}sector_price_earning_ratio?"
        f"date={annual_date}&exchange={exchange}&apikey={FMP_API_KEY}"
    )
    response = requests.get(url)
    response.raise_for_status()
    sector_list = response.json()
    for item in sector_list:
        if item.get("sector") == sector:
            return float(item.get("pe"))
    return None

def get_complete_metrics(ticker):
    # Get ratios data
    ratios_data = get_ratios(ticker)
    reporting_period = ratios_data.get("date")

    # Get key metrics and growth data
    metrics_data = get_key_metrics(ticker)
    growth_data = get_growth(ticker)

    # Get company profile for industry info
    profile_data = get_profile(ticker)
    sector = profile_data.get("sector")
    sector_pe = None
    if sector:
        try:
            sector_pe = yahoo_sector_pe(sector_name)
        except Exception as e:
            print(f"Warning: Couldn't fetch industry PE: {e}")

    # Get TTM financial ratios for more up-to-date metrics
    ttm_ratios = get_financial_ratios(ticker)

    # Create a comprehensive metrics dictionary
    metrics = {
        # Valuation Metrics
        "pe_ratio": ratios_data.get("peRatioTTM"),
        "sector_pe": sector_pe,
        "peg_ratio": ratios_data.get("pegRatioTTM"),
        "ps_ratio": ratios_data.get("priceToSalesRatioTTM"),
        "price_to_fcf": ratios_data.get("priceToFreeCashFlowsRatioTTM"),
        "earnings_yield": ratios_data.get("earningsYieldTTM"),
        #"fcf_yield": metrics_data.get("freeCashFlowYield"),

        # Profitability Metrics
        "roe": ratios_data.get("returnOnEquityTTM"),
        "roa": ratios_data.get("returnOnAssetsTTM"),
        "roic": ratios_data.get("returnOnInvestedCapitalTTM"),
        # "net_profit_margin": ratios_data.get("netProfitMargin"),
        "gross_profit_margin": ratios_data.get("grossProfitMarginTTM"),
        "operating_profit_margin": ratios_data.get("operatingProfitMarginTTM"),

        # Solvency/Leverage Metrics
        "debt_to_equity": ratios_data.get("debtToEquityTTM"),
        "debt_ratio": ratios_data.get("debtRatioTTM"),
        # "current_ratio": ratios_data.get("currentRatio"),
        "interest_coverage": ratios_data.get("interestCoverageTTM"),

        # Growth Metrics
        "revenue_growth": growth_data.get("revenueGrowth"),
        "eps_growth": growth_data.get("epsgrowth"),
        "operating_cash_flow_growth": growth_data.get("operatingCashFlowGrowth"),
        "fcf_growth": growth_data.get("freeCashFlowGrowth"),
        "capex_growth": growth_data.get("capitalExpenditureGrowth"),

        # Additional Information
        "enterprise_value": metrics_data.get("enterpriseValue"),
        "company_name": profile_data.get("companyName"),
        "industry": industry,
        "sector": profile_data.get("sector"),
        "market_cap": profile_data.get("mktCap"),
        "beta": profile_data.get("beta"),
        "ticker": ticker
    }

    return metrics


def define_metrics_importance(risk_tolerance, investment_goal):
    metrics = {
        "primary": [],     # Most important metrics (🔑)
        "secondary": [],   # Somewhat important metrics (🔹)
        "additional": []   # Less important but still relevant metrics (ℹ️)
    }

    # Conservative + Income
    if risk_tolerance == "Conservative" and investment_goal == "Income":
        metrics["primary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Lower P/E suggests better value"},
            {"key": "debt_ratio", "label": "Debt Ratio", "description": "Lower debt reduces risk"},
        ]
        metrics["secondary"] = [
        ]

    # Conservative + Balanced
    elif risk_tolerance == "Conservative" and investment_goal == "Balanced":
        metrics["primary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Lower P/E suggests better value"},
            {"key": "debt_ratio", "label": "Debt Ratio", "description": "Lower debt reduces risk"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Steady growth is preferred"}
        ]
        metrics["secondary"] = [
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Lower PEG indicates better value for growth"},
            {"key": "roe", "label": "Return on Equity", "description": "Shows management effectiveness"}
        ]
        metrics["additional"] = [
            {"key": "gross_profit_margin", "label": "Gross Profit Margin", "description": "Higher margins indicate pricing power"},
        ]

    # Conservative + Growth
    elif risk_tolerance == "Conservative" and investment_goal == "Growth":
        metrics["primary"] = [
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Lower PEG indicates better value for growth"},
            {"key": "debt_ratio", "label": "Debt Ratio", "description": "Lower debt reduces risk while pursuing growth"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Consistent growth without excessive volatility"}
        ]
        metrics["secondary"] = [
            {"key": "eps_growth", "label": "EPS Growth", "description": "Steady earnings growth with less volatility"},
            {"key": "roe", "label": "Return on Equity", "description": "Higher ROE suggests efficient growth"},
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Reasonable valuation for growth stocks"}
        ]
        metrics["additional"] = [
            {"key": "gross_profit_margin", "label": "Gross Profit Margin", "description": "Margin stability indicates sustainable growth"},
            {"key": "operating_cash_flow_growth", "label": "Operating Cash Flow Growth", "description": "Cash-backed growth is more reliable"}
        ]

    # Moderate + Income
    elif risk_tolerance == "Moderate" and investment_goal == "Income":
        metrics["primary"] = [
            {"key": "payout_ratio", "label": "Payout Ratio", "description": "Sustainable payout ratio ensures dividend longevity"},
        ]
        metrics["secondary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Value indicator relative to income potential"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Lower ratios indicate financial stability"},
        ]
        metrics["additional"] = [
            {"key": "roe", "label": "Return on Equity", "description": "Efficiency in generating profit from equity"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Moderate growth supports income increases"}
        ]

    # Moderate + Balanced
    elif risk_tolerance == "Moderate" and investment_goal == "Balanced":
        metrics["primary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Reasonable valuation relative to earnings"},
            {"key": "roe", "label": "Return on Equity", "description": "Shows management effectiveness"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Consistent top-line growth"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Reasonable leverage for growth and stability"}
        ]
        metrics["secondary"] = [
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Value indicator accounting for growth"},
        ]
        metrics["additional"] = [
            {"key": "operating_profit_margin", "label": "Operating Profit Margin", "description": "Operational efficiency"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Growth in shareholder earnings"}
        ]

    # Moderate + Growth
    elif risk_tolerance == "Moderate" and investment_goal == "Growth":
        metrics["primary"] = [
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Strong top-line growth potential"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Earnings growth translates to shareholder returns"},
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Lower indicates better value relative to growth"},
            {"key": "roic", "label": "Return on Invested Capital", "description": "Higher ROIC suggests effective growth investments"}
        ]
        metrics["secondary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Current valuation perspective"},
            {"key": "gross_profit_margin", "label": "Gross Profit Margin", "description": "Margin for reinvestment in growth"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Reasonable leverage for growth opportunities"}
        ]
        metrics["additional"] = [
            {"key": "operating_cash_flow_growth", "label": "Operating Cash Flow Growth", "description": "Cash generation supports sustainable growth"},
            {"key": "fcf_growth", "label": "Free Cash Flow Growth", "description": "Growing ability to fund future expansion"}
        ]

    # Aggressive + Income
    elif risk_tolerance == "Aggressive" and investment_goal == "Income":
        metrics["primary"] = [
            {"key": "earnings_yield", "label": "Earnings Yield", "description": "Higher indicates better income potential"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Growth supports dividend increases"},
            {"key": "roe", "label": "Return on Equity", "description": "Higher returns support income growth"}
        ]
        metrics["secondary"] = [
            {"key": "payout_ratio", "label": "Payout Ratio", "description": "Higher payout may provide more immediate income"},
            {"key": "net_profit_margin", "label": "Net Profit Margin", "description": "Higher margins support sustainable income"},
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Lower values indicate better income value"}
        ]
        metrics["additional"] = [
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Leverage can amplify returns if managed well"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Growth in earnings supports dividend growth"}
        ]

    # Aggressive + Balanced
    elif risk_tolerance == "Aggressive" and investment_goal == "Balanced":
        metrics["primary"] = [
            {"key": "roe", "label": "Return on Equity", "description": "Strong returns on shareholder capital"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Significant growth for appreciation potential"},
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Valuation context for potential returns"},
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Growth-adjusted valuation"}
        ]
        metrics["secondary"] = [
            {"key": "roic", "label": "Return on Invested Capital", "description": "Effectiveness of capital allocation"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Bottom-line growth potential"},
        ]
        metrics["additional"] = [
            {"key": "operating_profit_margin", "label": "Operating Profit Margin", "description": "Efficiency in operations"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Leverage amplifies returns in good times"}
        ]

    # Aggressive + Growth
    elif risk_tolerance == "Aggressive" and investment_goal == "Growth":
        metrics["primary"] = [
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "High growth potential is key"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Earnings growth driving shareholder returns"},
            {"key": "roic", "label": "Return on Invested Capital", "description": "Efficiency in generating growth from investments"},
            {"key": "gross_profit_margin", "label": "Gross Profit Margin", "description": "Margin for reinvestment in growth"}
        ]
        metrics["secondary"] = [
            {"key": "operating_cash_flow_growth", "label": "Operating Cash Flow Growth", "description": "Cash generation supports growth initiatives"},
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Growth-adjusted valuation metric"},
            {"key": "roe", "label": "Return on Equity", "description": "Efficiency in using shareholder capital"}
        ]
        metrics["additional"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Context for current valuation"},
            {"key": "fcf_growth", "label": "Free Cash Flow Growth", "description": "Ability to self-fund future growth"}
        ]

    # Default case
    else:
        metrics["primary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Price to Earnings ratio"},
            {"key": "roe", "label": "Return on Equity", "description": "Profitability relative to equity"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Top-line growth rate"},
            {"key": "debt_ratio", "label": "Debt Ratio", "description": "Lower values indicate less financial risk"}
        ]
        metrics["secondary"] = [
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "P/E ratio adjusted for growth"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Leverage ratio"},
        ]
        metrics["additional"] = [
            {"key": "operating_profit_margin", "label": "Operating Profit Margin", "description": "Operational efficiency"},
        ]

    return metrics

def format_metric_value(key, value):
    if value is None:
        return "N/A"

    # Format percentages
    if key in ["roe", "roa", "roic", "net_profit_margin", "gross_profit_margin",
               "operating_profit_margin", "revenue_growth", "eps_growth",
               "operating_cash_flow_growth", "fcf_growth", "capex_growth"]:
        return f"{value * 100:.2f}%" if isinstance(value, (int, float)) else "N/A"

    # Format ratios
    elif key in ["pe_ratio", "peg_ratio", "ps_ratio", "price_to_fcf",
                "debt_to_equity", "debt_ratio", "interest_coverage"]:
        return f"{value:.2f}x" if isinstance(value, (int, float)) else "N/A"

    # Format monetary values
    elif key in ["enterprise_value", "market_cap"]:
        if isinstance(value, (int, float)):
            if value >= 1e9:
                return f"${value / 1e9:.2f}B"
            elif value >= 1e6:
                return f"${value / 1e6:.2f}M"
            else:
                return f"${value:.2f}"
        else:
            return "N/A"


    # Format beta
    elif key == "beta" and isinstance(value, (int, float)):
        if value < 0.8:
            return f"{value:.2f} (Low)"
        elif value < 1.2:
            return f"{value:.2f} (Average)"
        else:
            return f"{value:.2f} (High)"

    # Default formatting
    else:
        return f"{value:.2f}" if isinstance(value, (int, float)) else "N/A"

def generate_terminal_table(metrics, metrics_importance, ticker):
    # Setup importance indicators with colors
    indicators = {
        "primary": f"{Fore.GREEN}🔑 MOST IMPORTANT{Style.RESET_ALL}",
        "secondary": f"{Fore.BLUE}🔹 IMPORTANT{Style.RESET_ALL}",
        "additional": f"{Fore.YELLOW}ℹ️  SUPPLEMENTARY{Style.RESET_ALL}"
    }

    # Company header
    output = f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n"
    output += f"{Fore.CYAN}FUNDAMENTAL ANALYSIS FOR: {metrics.get('company_name', 'Unknown')} ({ticker}){Style.RESET_ALL}\n"
    output += f"{Fore.CYAN}Industry: {metrics.get('industry', 'N/A')} | Sector: {metrics.get('sector', 'N/A')}{Style.RESET_ALL}\n"
    output += f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n\n"

    # Create tables for each importance category
    for category in ["primary", "secondary", "additional"]:
        if not metrics_importance[category]:
            continue

        output += f"{indicators[category]}\n\n"

        table_data = []
        headers = ["Metric", "Value", "Description"]

        for metric_def in metrics_importance[category]:
            key = metric_def["key"]
            value = metrics.get(key)
            formatted_value = format_metric_value(key, value)

            # Add benchmark comparison for PE ratio
            if key == "pe_ratio":
                industry_pe_formatted = format_metric_value("pe_ratio")

            # Add row to table
            table_data.append([
                metric_def["label"],
                formatted_value,
                metric_def["description"]
            ])

        # Generate and add table to output
        table = tabulate(table_data, headers=headers, tablefmt="grid")
        output += f"{table}\n\n"

    return output

def generate_preference_analysis_report(ticker, risk_tolerance, investment_goal):
    try:
        # Get all metrics
        all_metrics = get_complete_metrics(ticker)

        # Determine which metrics to emphasize
        metrics_importance = define_metrics_importance(risk_tolerance, investment_goal)

        # Generate the terminal table
        report = generate_terminal_table(all_metrics, metrics_importance, ticker)

        # Add summary
        report += f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n"
        report += f"{Fore.CYAN}PREFERENCE SUMMARY{Style.RESET_ALL}\n"
        report += f"{Fore.CYAN}Risk Tolerance: {risk_tolerance} | Investment Goal: {investment_goal}{Style.RESET_ALL}\n"
        report += f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n\n"

        # Create a custom summary based on user preferences
        summary = generate_custom_summary(all_metrics, risk_tolerance, investment_goal)
        report += summary

        return report

    except Exception as e:
        return f"Error generating report: {str(e)}"

def generate_custom_summary(metrics, risk_tolerance, investment_goal):
    company_name = metrics.get("company_name", "This company")
    summary = ""

    # Add risk profile assessment
    if risk_tolerance == "Conservative":
        if metrics.get("debt_ratio", 0) and metrics.get("debt_ratio", 0) > 0.5 and metrics.get("debt_ratio", 0) is not None:
            summary += f"{Fore.RED}⚠️ WARNING: {company_name} has a high debt ratio ({format_metric_value('debt_ratio', metrics.get('debt_ratio'))}) which may not align with your conservative risk profile.{Style.RESET_ALL}\n\n"
        if metrics.get("beta", 0) is not None and metrics.get("beta", 0) > 1.2 and metrics.get("beta", 0) is not None:
            summary += f"{Fore.RED}⚠️ WARNING: {company_name} has high volatility (Beta: {format_metric_value('beta', metrics.get('beta'))}) which may not align with your conservative risk profile.{Style.RESET_ALL}\n\n"

    # Add investment goal assessment
    if investment_goal == "Growth":
        if metrics.get("revenue_growth", 0) < 0.05 and metrics.get("revenue_growth", 0) is not None:
            summary += f"{Fore.YELLOW}📊 NOTE: {company_name} shows limited revenue growth ({format_metric_value('revenue_growth', metrics.get('revenue_growth'))}) which may not fully support your growth goal.{Style.RESET_ALL}\n\n"
        elif metrics.get("revenue_growth", 0) > 0.15 and metrics.get("revenue_growth", 0) is not None:
            summary += f"{Fore.GREEN}✅ POSITIVE: {company_name} demonstrates strong revenue growth ({format_metric_value('revenue_growth', metrics.get('revenue_growth'))}) which aligns with your growth goal.{Style.RESET_ALL}\n\n"


    # If no specific comments were added, provide a general statement
    if not summary:
        summary = f"Based on your {risk_tolerance.lower()} risk tolerance and {investment_goal.lower()} investment goal, review the metrics above to assess if {company_name} aligns with your investment strategy.\n\n"

    # Add final recommendation based on overall alignment
    alignment_score = calculate_alignment_score(metrics, risk_tolerance, investment_goal)
    if alignment_score > 75:
        summary += f"{Fore.GREEN}🌟 OVERALL: {company_name} appears to be well-aligned with your {risk_tolerance.lower()} risk tolerance and {investment_goal.lower()} investment goal.{Style.RESET_ALL}\n"
    elif alignment_score > 50:
        summary += f"{Fore.BLUE}🔹 OVERALL: {company_name} is moderately aligned with your {risk_tolerance.lower()} risk tolerance and {investment_goal.lower()} investment goal.{Style.RESET_ALL}\n"
    else:
        summary += f"{Fore.YELLOW}⚠️ OVERALL: {company_name} may not strongly align with your {risk_tolerance.lower()} risk tolerance and {investment_goal.lower()} investment goal. Consider the highlighted concerns.{Style.RESET_ALL}\n"

    return summary

def calculate_alignment_score(metrics, risk_tolerance, investment_goal):
    score = 50  # Start with neutral score

    # Adjust score based on risk tolerance
    if risk_tolerance == "Conservative":
        # Lower debt is better for conservative investors
        debt_ratio = metrics.get("debt_ratio")
        if debt_ratio is not None and debt_ratio < 0.3:
            score += 10
        elif debt_ratio is not None and debt_ratio > 0.5:
            score -= 10

        # Lower beta is better for conservative investors
        beta = metrics.get("beta")
        if beta is not None and beta < 0.8:
            score += 10
        elif beta is not None and beta > 1.2:
            score -= 10


    elif risk_tolerance == "Aggressive":
        # More growth-oriented metrics for aggressive investors
        rev_growth = metrics.get("revenue_growth")
        if rev_growth is not None and rev_growth > 0.15:
            score += 10
        elif rev_growth is not None and rev_growth < 0.05:
            score -= 5

        # Higher ROE is better for aggressive investors
        roe = metrics.get("roe")
        if roe is not None and roe > 0.20:
            score += 10
        elif roe is not None and roe < 0.1:
            score -= 5

    # Adjust score based on investment goal
    if investment_goal == "Income":

        # Lower payout ratio is more sustainable
        payout_ratio = metrics.get("payoutRatio")
        if payout_ratio is not None and payout_ratio < 0.7 and payout_ratio > 0:
            score += 5
        elif payout_ratio is not None and (payout_ratio > 0.9 or payout_ratio < 0):
            score -= 10

    elif investment_goal == "Growth":
        # Higher growth rates are better
        rev_growth = metrics.get("revenue_growth")
        if rev_growth is not None and rev_growth > 0.15:
            score += 15
        elif rev_growth is not None and rev_growth < 0.05:
            score -= 15

        # Higher EPS growth is important
        eps_growth = metrics.get("eps_growth")
        if eps_growth is not None and eps_growth > 0.15:
            score += 10
        elif eps_growth is not None and eps_growth < 0.05:
            score -= 10

    # Ensure score stays within bounds
    return max(0, min(100, score))
