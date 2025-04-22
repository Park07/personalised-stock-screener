import base64
from functools import lru_cache
import io
import json
import logging
from colorama import Fore, Style, init
import matplotlib.pyplot as plt
import pandas as pd
import math
import traceback
from matplotlib.patches import Wedge
import plotly.graph_objects as go
import numpy as np
import requests
from tabulate import tabulate
import yfinance as yf
import functools
import time
import threading
import redis
SECTOR_PE_CACHE = {}
SECTOR_PE_CACHE_TIMESTAMP = {}
CACHE_EXPIRY = 24 * 60 * 60 

from config import FMP_API_KEY


BASE_URL = "https://financialmodelingprep.com/api/v3/"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"
WIKI_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# Enhanced API calling functions with debugging and fallbacks

# redis for faster caching
DEFAULT_SECTOR_PE_VALUES = {
    "Technology": 34.4,
    "Information Technology": 34.4,
    "Healthcare": 22.5,
    "Health Care": 22.5,
    "Consumer Cyclical": 24.3,
    "Consumer Discretionary": 24.3,
    "Consumer Defensive": 20.1,
    "Consumer Staples": 20.1,
    "Financial Services": 15.2,
    "Financials": 15.2,
    "Industrials": 18.7,
    "Basic Materials": 16.8,
    "Materials": 16.8,
    "Real Estate": 19.5,
    "Communication Services": 21.3,
    "Energy": 16.2,
    "Utilities": 18.4
}

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_EXPIRY = 86400  # 24 hours in seconds

# Cache keys and prefix for organization
REDIS_KEY_PREFIX = "stock_metrics:"
SECTOR_PE_KEY = lambda sector: f"{REDIS_KEY_PREFIX}sector_pe:{sector}"
UPDATE_LOCK_KEY = lambda sector: f"{REDIS_KEY_PREFIX}sector_pe_update_lock:{sector}"

# Singleton Redis client
_redis_client = None

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
                url = (
                    f"{BASE_URL}{endpoint}-ttm/{ticker}"
                    f"?apikey={FMP_API_KEY}"
                )
            else:
                url = (
                    f"{BASE_URL}{endpoint}/{ticker}"
                    f"?period=annual&apikey={FMP_API_KEY}"
                )
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data[0]
        except Exception as e:
            print(f"DEBUG: Error with {endpoint}" +
                  ("-ttm" if is_ttm else "") + f": {e}")
    # If we get here, all endpoints failed
    print(f"WARNING: {error_message}: All endpoints failed")
    return {}

@lru_cache(maxsize=128)
def get_ratios(ticker):
    """Get financial ratios with fallback from TTM to annual"""
    endpoint_types = [
        ("ratios", True),   # Try TTM first
        ("ratios", False)   # Fall back to annual just in case
    ]
    return fetch_data_with_fallback(
        ticker, endpoint_types, "Error fetching ratios data")

@lru_cache(maxsize=128)
def get_key_metrics(ticker):
    """Get key metrics with fallback from TTM to annual"""
    endpoint_types = [
        ("key-metrics", True),   # Try TTM first
        ("key-metrics", False)   # Fall back to annual
    ]
    return fetch_data_with_fallback(
        ticker,
        endpoint_types,
        "Error fetching key metrics data")

@lru_cache(maxsize=128)
def get_growth(ticker):
    """Gets REAL financial growth data from API with enhanced logging."""
    logging.debug(f"FUNDAMENTALS: --- Calling get_growth for {ticker} ---")
    # Using annual financial-growth endpoint, limit=1 gets the latest year
    url = f"{BASE_URL}financial-growth/{ticker}?period=annual&limit=1&apikey={FMP_API_KEY}"
    default_return = {'revenue_growth': None, 'earnings_growth': None}
    response = None # Define response here to access it in except block

    try:
        logging.debug(f"FUNDAMENTALS: Requesting Growth URL: {url}")
        response = requests.get(url, timeout=12) # Slightly longer timeout
        status_code = response.status_code
        logging.info(f"FUNDAMENTALS: Growth request for {ticker} Status: {status_code}") # Log status

        # Check for non-200 status codes BEFORE trying .json()
        if status_code != 200:
            response_text_snippet = response.text[:300] # Get first part of error message
            log_msg = f"FUNDAMENTALS: Growth HTTP Error for {ticker}: {status_code}. Response: {response_text_snippet}"
            if status_code == 401: logging.error(log_msg + " (Check API Key)")
            elif status_code == 429: logging.error(log_msg + " (Rate Limit Exceeded!)")
            else: logging.warning(log_msg) # Log other non-200 as warnings
            return default_return # Return default on HTTP error

        # Try parsing JSON *after* checking status is 200
        try:
            data = response.json()
        except json.JSONDecodeError as json_e:
            logging.error(f"FUNDAMENTALS: JSONDecodeError parsing growth for {ticker}: {json_e}. Response text: {response.text[:300]}")
            return default_return

        # Check if data is a non-empty list
        if data and isinstance(data, list) and len(data) > 0:
            growth_data = data[0] # Get the first element
            logging.debug(f"FUNDAMENTALS: Raw growth_data received for {ticker}: {growth_data}")

            # Define the EXACT keys expected from FMP API (based on your previous sample)
            revenue_key = 'revenueGrowth'
            eps_key = 'epsgrowth' 

            extracted_data = {
                'revenue_growth': growth_data.get(revenue_key),
                'earnings_growth': growth_data.get(eps_key),
             }

            logging.info(f"FUNDAMENTALS: Extracted growth for {ticker}: Rev={extracted_data['revenue_growth']}, EPS={extracted_data['earnings_growth']}")

            # Optional: Add warnings if specific keys were missing
            if extracted_data['revenue_growth'] is None:
                logging.warning(f"FUNDAMENTALS: Key '{revenue_key}' missing/null in growth data for {ticker}.")
            if extracted_data['earnings_growth'] is None:
                logging.warning(f"FUNDAMENTALS: Key '{eps_key}' missing/null in growth data for {ticker}.")

            return extracted_data
        else:
            # Log if API returned empty list [] or something unexpected
            logging.warning(f"FUNDAMENTALS: Empty data list or non-list received for growth {ticker}. Response: {data}")
            return default_return

    except requests.exceptions.Timeout:
        logging.error(f"FUNDAMENTALS: Timeout fetching growth for {ticker}")
        return default_return
    except requests.exceptions.RequestException as req_e:
        # This catches connection errors, DNS errors etc.
        logging.error(f"FUNDAMENTALS: RequestException fetching growth for {ticker}: {req_e}")
        return default_return
    except Exception as e:
        # Catch any other unexpected error
        logging.exception(f"FUNDAMENTALS: Unexpected error in get_growth for {ticker}")
        return default_return
    
@lru_cache(maxsize=128)
def get_ev_ebitda(ticker):
    try:
        metrics = get_key_metrics(ticker) 
        ev_ebitda = metrics.get('enterpriseValueOverEBITDATTM')
        return float(ev_ebitda) if ev_ebitda is not None else None
    except Exception:
        return None

@lru_cache(maxsize=128)
def get_profile(ticker):
    """Get company profile"""
    url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
    print(f"🔍 get_profile fetching: {url!r}")
    try:
        response = requests.get(url, timeout=10)
        print(f"   → status: {response.status_code}")
        if response.status_code != 200:
            print(f"   → body: {response.text!r}")
            response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError("Empty response returned for profile")
        return data[0]
    except Exception as e:
        print(f"⚠️ WARNING: Error fetching profile data for {ticker}: {e}")
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
    return mapped_sector or fmp_sector


def get_key_metrics_summary(ticker: str) -> dict:
    """
    Get key metrics

    """
    # Get ratios data - try both TTM and annual
    ratios_data = get_ratios(ticker)
    # Try different field name conventions
    pe = ratios_data.get("peRatioTTM") or ratios_data.get("priceEarningsRatio")
    peg = ratios_data.get("pegRatioTTM") or ratios_data.get(
        "priceEarningsToGrowthRatio")
    ps = ratios_data.get("priceToSalesRatioTTM") or ratios_data.get(
        "priceToSalesRatio")
    roe = ratios_data.get(
        "returnOnEquityTTM") or ratios_data.get("returnOnEquity")
    debt = ratios_data.get("debtRatioTTM") or ratios_data.get("debtRatio")
    # Get key metrics  ttm is more ideal but if (x) work -> use alt.
    metrics_data = get_key_metrics(ticker)
    enterprise_value = metrics_data.get(
        "enterpriseValueTTM") or metrics_data.get("enterpriseValue")
    free_cash_flow_yield = (
        metrics_data.get("freeCashFlowYieldTTM")
        or metrics_data.get("freeCashFlowYield")
    )
    # Get growth data (annual only)
    growth_data = get_growth(ticker)
    rev_growth = growth_data.get("revenueGrowth")
    eps_growth = growth_data.get("epsgrowth") or growth_data.get("epsGrowth")
    # Get company profile for sector information
    profile_data = get_profile(ticker)
    fmp_sector = profile_data.get("sector")
    sector = map_sector_name(fmp_sector)
    # Get sector PE
    sector_pe = None
    if sector:
        try:
            sector_pe = get_sector_pe_redis(sector)
            print(f"info success")
        except Exception as e:
            print(f"WARNING: Couldn't fetch sector PE: {e}")
    # Build result dictionary
    result_dict = {
        "pe": round(pe, 2),
        "sector_pe": round(sector_pe, 2),
        "peg": peg,
        "ps": ps,
        "roe": roe,
        "debtRatio": debt,
        "enterpriseValue": enterprise_value,
        "freeCashFlowYield": free_cash_flow_yield,
        "revenueGrowth": rev_growth,
        "epsGrowth": eps_growth
    }
    return result_dict


@lru_cache(maxsize=1)
def _sp500_companies() -> pd.DataFrame:
    # Fetch S&P 500 companies data from Wikipedia with improved column
    # handling.
    tables = pd.read_html(WIKI_SP500_URL, flavor="bs4")
    first_table = tables[0]
    # Look for GICS Sector column with different possible formats
    gics_col = None
    for col in first_table.columns:
        if 'GICS' in str(col) and 'Sector' in str(col):
            gics_col = col
            break
    if not gics_col:
        # debugging
        gics_col = first_table.columns[1]
    # Create DataFrame with normalised column names
    df = tables[0][["Symbol", gics_col]]
    df.columns = ["ticker", "sector"]
    # Normalise sector names by stripping whitespace
    df["sector"] = df["sector"].str.strip()
    # Debug: Print unique sectors found
    return df

def get_redis_client():
    """Get or create Redis client singleton"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                socket_timeout=2,  # Short timeout to prevent blocking UI
                decode_responses=True  # Auto-decode to Python strings
            )
            # Test connection
            _redis_client.ping()
            print("INFO: Successfully connected to Redis")
        except Exception as e:
            print(f"WARNING: Redis connection failed: {e}")
            _redis_client = None
    return _redis_client

def get_sector_pe_redis(sector):
    """
    Get sector PE with Redis caching for maximum performance.
    Falls back to default values if Redis is unavailable or no cached value exists.
    
    This function runs in O(1) time in the normal case (cached hit).
    """
    if not sector:
        return None
        
    # Map sector name if needed
    mapped_sector = map_sector_name(sector)
    key = SECTOR_PE_KEY(mapped_sector)
    
    # Try to get from Redis cache first (fastest path)
    redis_client = get_redis_client()
    if redis_client:
        try:
            cached_value = redis_client.get(key)
            if cached_value:
                sector_pe = float(cached_value)
                print(f"INFO: Using Redis cached PE value {sector_pe} for sector '{mapped_sector}'")
                return sector_pe
                
            # Value not in cache, check if update is already scheduled
            update_lock_key = UPDATE_LOCK_KEY(mapped_sector)
            if not redis_client.exists(update_lock_key):
                # Set lock to prevent duplicate update requests
                redis_client.setex(update_lock_key, 300, "updating")  # Lock for 5 minutes
                
                # Schedule background update
                print(f"INFO: Scheduling background update for sector '{mapped_sector}'")
                thread = threading.Thread(
                    target=update_sector_pe_in_background, 
                    args=(mapped_sector,)
                )
                thread.daemon = True  # Don't keep process alive for this thread
                thread.start()
        except Exception as e:
            print(f"WARNING: Redis error: {e}")
    
    # If not in Redis or Redis unavailable, use default value
    if mapped_sector in DEFAULT_SECTOR_PE_VALUES:
        default_pe = DEFAULT_SECTOR_PE_VALUES[mapped_sector]
        print(f"INFO: Using default PE {default_pe} for sector '{mapped_sector}'")
        return default_pe
    
    # Final fallback
    return 21.0  # Average market PE

def update_sector_pe_in_background(sector):
    """
    Update the Redis cache with fresh sector PE values.
    This is the slow operation that runs in a background thread.
    """
    if not sector:
        return
        
    redis_client = get_redis_client()
    if not redis_client:
        print("WARNING: Cannot update sector PE - Redis unavailable")
        return
        
    try:
        print(f"BACKGROUND: Starting calculation of PE for sector '{sector}'")
        
        # Calculate the real sector PE - this is the slow operation
        sector_pe = yahoo_sector_pe(sector)
        
        if sector_pe is not None:
            # Store in Redis with expiration
            key = SECTOR_PE_KEY(sector)
            redis_client.setex(key, REDIS_EXPIRY, str(sector_pe))
            print(f"BACKGROUND: Updated Redis PE value {sector_pe:.2f} for sector '{sector}'")
            
        # Release the update lock
        update_lock_key = UPDATE_LOCK_KEY(sector)
        redis_client.delete(update_lock_key)
        
    except Exception as e:
        print(f"BACKGROUND: Error updating sector PE: {e}")
        
        # Always release the lock even on failure
        try:
            if redis_client:
                update_lock_key = UPDATE_LOCK_KEY(sector)
                redis_client.delete(update_lock_key)
        except Exception as lock_e:
            print(f"BACKGROUND: Error releasing lock: {lock_e}")
            

@functools.lru_cache(maxsize=32)
def yahoo_ticker_info(ticker):
    """
    Cached function to get ticker info from Yahoo Finance
    This helps avoid repeated API calls for the same ticker
    """
    return yf.Ticker(ticker).info

@functools.lru_cache(maxsize=11)  # 11 standard S&P 500 sectors
def yahoo_sector_pe(sector: str) -> float | None:
    """
    Market‑cap‑weighted trailing‑12‑month P/E for all S&P‑500 stocks in a sector.
    Uses a tiered caching strategy to minimize API calls:
    1. Check if we have a non-expired cached value for the whole sector
    2. Use cached ticker info for individual stocks
    """
    # Check the in-memory cache first (with expiration)
    current_time = time.time()
    if sector in SECTOR_PE_CACHE and current_time - SECTOR_PE_CACHE_TIMESTAMP.get(sector, 0) < CACHE_EXPIRY:
        print(f"INFO: Using cached PE value for sector '{sector}'")
        return SECTOR_PE_CACHE[sector]
    
    print(f"INFO: Calculating PE for sector '{sector}'")
    try:
        # Get tickers for the sector
        df = _sp500_companies()
        tickers = df.loc[df["sector"] == sector, "ticker"].tolist()
        if not tickers:
            raise ValueError(f"No S&P‑500 tickers found for sector '{sector}'")

        # Use a sample of tickers for large sectors to improve performance
        # This is a tradeoff between accuracy and speed
        if len(tickers) > 30:
            import random
            random.seed(42)  # For reproducibility
            print(f"INFO: Sampling 30 stocks from {len(tickers)} in sector '{sector}'")
            tickers = random.sample(tickers, 30)
        
        records = []
        for tkr in tickers:
            try:
                # Use cached ticker info
                info = yahoo_ticker_info(tkr)
                mc = info.get("marketCap")
                eps = info.get("trailingEps")
                sh = info.get("sharesOutstanding")
                if mc and eps and sh and eps != 0:
                    net_income = eps * sh  # EPS * shares = trailing NI
                    records.append({"mc": mc, "ni": net_income})
            except Exception as e:
                print(f"WARNING: Error processing ticker {tkr}: {e}")
                continue

        if not records:
            print(f"WARNING: No valid records found for sector '{sector}'")
            return None
            
        sector_mc = sum(r["mc"] for r in records)
        sector_ni = sum(r["ni"] for r in records)
        sector_pe = sector_mc / sector_ni if sector_ni else None
        
        # Store in cache with timestamp
        if sector_pe is not None:
            SECTOR_PE_CACHE[sector] = sector_pe
            SECTOR_PE_CACHE_TIMESTAMP[sector] = current_time
            print(f"INFO: Cached PE value {sector_pe:.2f} for sector '{sector}'")
        
        return sector_pe
    
    except Exception as e:
        print(f"ERROR: Failed to calculate sector PE: {e}")
        return None


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
        dcf_url = (
            f"{BASE_URL}discounted-cash-flow/{ticker}"
            f"?apikey={FMP_API_KEY}"
        )
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
            valuation_data['company_name'] = company_data[0].get(
                'companyName', ticker)
            # Use company price as current price if DCF price not available
            if valuation_data['current_price'] == 0:
                valuation_data['current_price'] = company_data[0].get(
                    'price', 0)
            valuation_data['market_cap'] = company_data[0].get('mktCap', 0)
        print(f"INFO: Successfully retrieved valuation data for {ticker}")
        return valuation_data
    except Exception as e:
        print(f"ERROR: Failed to fetch FMP valuation data: {e}")
        return None


def generate_pe_gauge_plotly(
        company_pe,
        market_pe,
        company_name="Company",
        dark_theme=True):
    # Handle None or invalid values
    if company_pe is None or not isinstance(
            company_pe, (int, float)) or company_pe <= 0:
        company_pe = 0.1
    if market_pe is None or not isinstance(
            market_pe, (int, float)) or market_pe <= 0:
        market_pe = 0.1

    # Set colors based on theme
    if dark_theme:
        bg_color = '#1a1a2e'
        text_color = 'white'
        paper_bgcolor = '#1a1a2e'
        plot_bgcolor = '#1a1a2e'
        company_color = '#3498db'  # Blue for company
        market_color = '#2ecc71'   # Green for market
    else:
        bg_color = '#ffffff'
        text_color = 'black'
        paper_bgcolor = '#ffffff'
        plot_bgcolor = '#f8f9fa'
        company_color = '#2980b9'  # Darker blue for company
        market_color = '#27ae60'   # Darker green for market

    # Determine gauge range
    max_pe = max(company_pe, market_pe)
    # Round to nearest 10, at least 60
    gauge_max = max(60, round(max_pe * 1.2, -1))

    # Create gauge steps
    steps = []

    # Define color steps based on PE ranges
    if gauge_max <= 60:
        steps = [
            {'range': [0, 10], 'color': '#4dab6d'},     # Green
            {'range': [10, 20], 'color': '#72c66e'},    # Light green
            {'range': [20, 30], 'color': '#c1da64'},    # Yellow-green
            {'range': [30, 40], 'color': '#f6ee54'},    # Yellow
            {'range': [40, 50], 'color': '#fabd57'},    # Orange
            {'range': [50, 60], 'color': '#ee4d55'}     # Red
        ]
        # Filter steps based on gauge_max
        steps = [step for step in steps if step['range'][0] < gauge_max]
        # Adjust the last step to match gauge_max
        if steps:
            steps[-1]['range'][1] = gauge_max
    else:
        # For higher PE values, create proportional steps
        step_size = gauge_max // 6
        colors = [
            '#4dab6d',
            '#72c66e',
            '#c1da64',
            '#f6ee54',
            '#fabd57',
            '#ee4d55']
        texts = [
            'Undervalued',
            'Fair Value',
            'Growth',
            'Premium',
            'Expensive',
            'Very Expensive']

        for i in range(6):
            start = i * step_size
            end = (i + 1) * step_size if i < 5 else gauge_max
            steps.append({
                'range': [start, end],
                'color': colors[i]
            })

    # Create the gauge figure
    fig = go.Figure()

    # Add the company PE gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=company_pe,
            title={
                'text': (
                    f"<b>{company_name} PE Ratio</b><br>"
                    f"<span style='color:{company_color}'>Company: {company_pe:.1f}x</span> | "
                    f"<span style='color:{market_color}'>Market: {market_pe:.1f}x</span>"
                ),
                'font': {
                    'color': text_color,
                    'size': 16}},
            gauge={
                'axis': {
                    'range': [
                        0,
                        gauge_max],
                    'ticksuffix': 'x',
                    'tickfont': {
                        'color': text_color}},
                'bar': {
                    'color': company_color},
                'steps': steps,
                'threshold': {
                    'line': {
                        'color': market_color,
                        'width': 4},
                    'thickness': 0.75,
                    'value': market_pe}},
            number={
                'suffix': 'x',
                'font': {
                    'color': text_color}},
            domain={
                'x': [
                    0,
                    1],
                'y': [
                    0,
                    1]}))

    # Update layout
    fig.update_layout(
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        font={'color': text_color, 'family': 'Arial'},
        margin={"l": 40, "r": 40, "t": 60, "b": 40},
        height=350,
        width=500
    )

    # Convert to image
    img_bytes = fig.to_image(format="png", engine="kaleido")
    img_str = base64.b64encode(img_bytes).decode('utf-8')

    return img_str

# Add this to your Flask routes


def generate_pe_plotly_endpoint(ticker, pe_ratio, sector_pe, dark_theme=True):
    """Generate PE gauge chart using Plotly for a given ticker"""
    try:
        # Ensure values are numbers
        if pe_ratio is None:
            pe_ratio = 0
        if sector_pe is None:
            sector_pe = 0

        pe_ratio = float(pe_ratio)
        sector_pe = float(sector_pe)

        # Generate the gauge chart
        img_str = generate_pe_gauge_plotly(
            pe_ratio, sector_pe, ticker, dark_theme)
        return img_str
    except Exception as e:
        print(f"ERROR: Failed to generate Plotly PE chart: {str(e)}")
        print(traceback.format_exc())
        return None

def warm_sector_pe_cache():
    """
    Pre-warm the Redis cache with sector PE values for common sectors.
    Call this when your application starts.
    """
    common_sectors = [
        "Information Technology", 
        "Health Care",
        "Financials",
        "Consumer Discretionary",
        "Communication Services"
    ]
    
    print("INFO: Pre-warming sector PE cache...")
    for sector in common_sectors:
        # Just calling this will trigger background updates if needed
        get_sector_pe_redis(sector)
    
    print("INFO: Sector PE cache pre-warming complete")
