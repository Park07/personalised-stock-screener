import json
import requests
import logging
from tabulate import tabulate
from colorama import Fore, Style, init
from config import FMP_API_KEY
from functools import lru_cache
import yfinance as yf
import pandas as pd
import io
import matplotlib.pyplot as plt
import base64



BASE_URL = "https://financialmodelingprep.com/api/v3/"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"
WIKI_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# Enhanced API calling functions with debugging and fallbacks

def fetch_data_with_fallback(ticker, endpoint_types, error_message):
    """
    Try multiple endpoint types and return the first successful result.
    
    Args:
        ticker: The stock ticker symbol
        endpoint_types: List of tuples (endpoint, is_ttm) to try in order
        error_message: Error message to display if all endpoints fail
    
    Returns:
        The first successful API response or default {}
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
    Maps sector names from FMP API to standard S&P 500 sector names.
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

def get_key_metrics(ticker: str) -> dict:
    """
    Get key metrics

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
        "pe": roun(pe),
        "sector_pe": round(sector_pe),
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
        # debugging
        gics_col = first_table.columns[1]
        print(f"DEBUG: Falling back to column at index 1: '{gics_col}'")
    
    # Create DataFrame with normalised column names
    df = tables[0][["Symbol", gics_col]]
    df.columns = ["ticker", "sector"]
    
    # Normalise sector names by stripping whitespace
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


# fetch sector P/E instead of sector P/E
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

# using dcf to calculating the intrinsic value:
def get_fmp_valuation_data(ticker):
    """Get valuation data from Financial Modeling Prep API"""
    print(f"INFO: Fetching valuation data for {ticker} from FMP")
    
    try:
        # Fetch DCF valuation data
        dcf_url = f"{BASE_URL}discounted-cash-flow/{ticker}?apikey={FMP_API_KEY}"
        print(f"DEBUG: Fetching DCF data from FMP")
        dcf_response = requests.get(dcf_url, timeout=15)
        dcf_data = dcf_response.json()
        
        # Get company profile data
        company_url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
        company_response = requests.get(company_url, timeout=10)
        company_data = company_response.json()
        
        # Extract and combine all valuation data
        valuation_data = {
            'ticker': ticker,
            'company_name': ticker,  
            'current_price': 0,
            'fair_value': 0,
            'date': '',
            'market_cap': 0
        }
        
        # Extract DCF valuation data
        if dcf_data and len(dcf_data) > 0:
            valuation_data['fair_value'] = dcf_data[0].get('dcf', 0)
            valuation_data['date'] = dcf_data[0].get('date', '')
            valuation_data['current_price'] = dcf_data[0].get('price', 0)
        
        # Extract company profile data
        if company_data and len(company_data) > 0:
            valuation_data['company_name'] = company_data[0].get('companyName', ticker)
            # Use company price as current price if DCF price not available
            if valuation_data['current_price'] == 0:
                valuation_data['current_price'] = company_data[0].get('price', 0)
            valuation_data['market_cap'] = company_data[0].get('mktCap', 0)
        
        print(f"INFO: Successfully retrieved valuation data for {ticker}")
        print(f"DEBUG: Fair value: ${valuation_data['fair_value']:.2f}, Current price: ${valuation_data['current_price']:.2f}")
        
        return valuation_data
        
    except Exception as e:
        print(f"ERROR: Failed to fetch FMP valuation data: {e}")
        return None

def generate_valuation_gauge_chart(ticker, dark_theme=True):
    """Generate a visual valuation gauge showing undervalued/overvalued status."""
    print(f"INFO: Generating valuation gauge for {ticker}")
    
    try:
        valuation_data = get_fmp_valuation_data(ticker)
        if valuation_data is None:
            print(f"ERROR: Could not retrieve valuation data for {ticker}")
            return None
        
        # Extract valuation metrics
        current_price = valuation_data['current_price']
        fair_value = valuation_data['fair_value']
        company_name = valuation_data['company_name']
        
        # Determine if undervalued/overvalued and by how much
        if current_price > 0 and fair_value > 0:
            potential = ((fair_value / current_price) - 1) * 100
            is_undervalued = potential >= 0
        else:
            potential = 0
            is_undervalued = False
        
        # Setup chart theme
        if dark_theme:
            plt.style.use('dark_background')
            background_color = '#1e2130'
            text_color = 'white'
            value_color = '#4daf4a' if is_undervalued else '#e41a1c'  # Green for undervalued, red for overvalued
            gauge_colors = ['#4daf4a', '#95cc79', '#ffeda0', '#feb24c', '#f03b20']  # Green to red
        else:
            plt.style.use('default')
            background_color = '#f8f9fa'
            text_color = '#333333'
            value_color = '#4daf4a' if is_undervalued else '#e41a1c'
            gauge_colors = ['#4daf4a', '#95cc79', '#ffeda0', '#feb24c', '#f03b20']
        
        # Create figure with a custom aspect ratio
        fig = plt.figure(figsize=(8, 10), facecolor=background_color)
        
        # Use GridSpec for more control over layout
        gs = plt.GridSpec(5, 1, height_ratios=[1, 0.5, 2, 2, 0.5])
        
        # Title area
        ax_title = fig.add_subplot(gs[0])
        ax_title.axis('off')
        ax_title.text(0.5, 0.5, f"{company_name} Valuation Analysis", 
                     ha='center', va='center', fontsize=22, fontweight='bold', color=text_color)
        
        # Valuation status
        ax_status = fig.add_subplot(gs[1])
        ax_status.axis('off')
        status_text = f"{abs(potential):.1f}% {'Undervalued' if is_undervalued else 'Overvalued'}"
        ax_status.text(0.5, 0.5, status_text, ha='center', va='center', 
                      fontsize=28, fontweight='bold', color=value_color)
        
        # Create the gauge visualization
        ax_gauge = fig.add_subplot(gs[2])
        ax_gauge.axis('off')
        
        # Draw gauge background
        gauge_height = 0.6
        gauge_width = 0.9
        gauge_y = 0.2
        
        # Create a gradient background for the gauge
        gauge_segments = 5
        segment_width = gauge_width / gauge_segments
        
        for i in range(gauge_segments):
            x_pos = (1 - gauge_width) / 2 + i * segment_width
            rect = plt.Rectangle((x_pos, gauge_y), segment_width, gauge_height, 
                                facecolor=gauge_colors[i], alpha=0.7, edgecolor='none')
            ax_gauge.add_patch(rect)
        
        # Add labels
        ax_gauge.text(0.1, gauge_y - 0.05, "Undervalued", fontsize=12, ha='center', va='top', color=gauge_colors[0])
        ax_gauge.text(0.9, gauge_y - 0.05, "Overvalued", fontsize=12, ha='center', va='top', color=gauge_colors[-1])
        
        # Calculate marker position based on valuation
        # Map potential from -50% to +100% to the gauge position
        min_potential = -50
        max_potential = 100
        
        # Clamp potential to range and map to 0-1
        clamped_potential = max(min(potential, max_potential), min_potential)
        normalized_position = (clamped_potential - min_potential) / (max_potential - min_potential)
        
        # Map to gauge width
        marker_x = (1 - gauge_width) / 2 + normalized_position * gauge_width
        
        # Draw marker pointer (triangle)
        marker_y = gauge_y + gauge_height
        marker_width = 0.04
        marker_height = 0.08
        
        triangle = plt.Polygon([[marker_x, marker_y], 
                               [marker_x - marker_width, marker_y + marker_height],
                               [marker_x + marker_width, marker_y + marker_height]], 
                              facecolor='white', edgecolor='gray')
        ax_gauge.add_patch(triangle)
        
        # Draw marker line
        ax_gauge.axvline(x=marker_x, ymin=0.1, ymax=0.95, color='white', linestyle='--', alpha=0.5, linewidth=1)
        
        # Price vs Fair Value section
        ax_values = fig.add_subplot(gs[3])
        ax_values.axis('off')
        
        # Format numbers with appropriate suffixes
        def format_large_number(num):
            if num >= 1e12:
                return f"${num/1e12:.2f}T"
            elif num >= 1e9:
                return f"${num/1e9:.2f}B"
            elif num >= 1e6:
                return f"${num/1e6:.2f}M"
            elif num >= 1e3:
                return f"${num/1e3:.2f}K"
            else:
                return f"${num:.2f}"
        
        # Show current price and fair value
        current_price_text = format_large_number(current_price)
        fair_value_text = format_large_number(fair_value)
        
        # Calculate y positions
        value_box_y = 0.6
        value_box_height = 0.3
        
        # Draw value boxes with labels
        # Current Price Box
        current_price_rect = plt.Rectangle((0.1, value_box_y), 0.35, value_box_height, 
                                          facecolor='#2c3e50', alpha=0.5, edgecolor='gray')
        ax_values.add_patch(current_price_rect)
        ax_values.text(0.1 + 0.35/2, value_box_y + value_box_height + 0.05, 
                      "Current Price", ha='center', va='bottom', fontsize=14, color=text_color)
        ax_values.text(0.1 + 0.35/2, value_box_y + value_box_height/2, 
                      current_price_text, ha='center', va='center', fontsize=18, 
                      fontweight='bold', color=text_color)
        
        # Fair Value Box
        fair_value_rect = plt.Rectangle((0.55, value_box_y), 0.35, value_box_height, 
                                       facecolor=value_color, alpha=0.4, edgecolor='gray')
        ax_values.add_patch(fair_value_rect)
        ax_values.text(0.55 + 0.35/2, value_box_y + value_box_height + 0.05, 
                      "Fair Value", ha='center', va='bottom', fontsize=14, color=text_color)
        ax_values.text(0.55 + 0.35/2, value_box_y + value_box_height/2, 
                      fair_value_text, ha='center', va='center', fontsize=18, 
                      fontweight='bold', color=text_color)
        
        # Add potential upside/downside
        potential_text = f"{'Upside' if is_undervalued else 'Downside'} Potential: {abs(potential):.1f}%"
        ax_values.text(0.5, value_box_y - 0.1, potential_text, ha='center', va='top', 
                      fontsize=16, fontweight='bold', color=value_color)
        
        # Add market cap if available
        if valuation_data['market_cap'] > 0:
            market_cap_text = f"Market Cap: {format_large_number(valuation_data['market_cap'])}"
            ax_values.text(0.5, 0.2, market_cap_text, ha='center', va='top', 
                          fontsize=14, color=text_color)
        
        # Add footer with source and date
        ax_footer = fig.add_subplot(gs[4])
        ax_footer.axis('off')
        source_text = "Source: FMP Discounted Cash Flow Analysis"
        
        ax_footer.text(0.05, 0.5, source_text, ha='left', va='center', 
                      fontsize=10, color=text_color, alpha=0.7)

        
        plt.subplots_adjust(hspace=0, top=0.95, bottom=0.05, left=0.05, right=0.95)
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, facecolor=background_color, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to base64
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        print("INFO: Valuation gauge chart generated successfully")
        return img_str
        
    except Exception as e:
        print(f"ERROR: Failed to generate valuation gauge: {e}")
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
