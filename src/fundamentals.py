import base64
from functools import lru_cache
import io
import json
import logging
from colorama import Fore, Style, init
import matplotlib.pyplot as plt
import pandas as pd
import traceback
from matplotlib.patches import Wedge
import plotly.graph_objects as go
import numpy as np
import requests
from tabulate import tabulate
import yfinance as yf

from .config import FMP_API_KEY


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


def get_ratios(ticker):
    """Get financial ratios with fallback from TTM to annual"""
    endpoint_types = [
        ("ratios", True),   # Try TTM first
        ("ratios", False)   # Fall back to annual just in case
    ]
    return fetch_data_with_fallback(
        ticker, endpoint_types, "Error fetching ratios data")


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


def get_growth(ticker):
    """Get financial growth data"""
    endpoint_types = [
        ("financial-growth", False)  # Only annual makes sense for growth
    ]
    return fetch_data_with_fallback(
        ticker, endpoint_types, "Error fetching growth data")


def get_profile(ticker):
    """Get company profile"""
    try:
        url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
        response = requests.get(url)
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(
                f"{response.status_code} {response.reason}")
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
            sector_pe = yahoo_sector_pe(sector)
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


def yahoo_sector_pe(sector: str) -> float | None:
    # Market‑cap‑weighted trailing‑12‑month P/E for all S&P‑500 stocks in
    # `sector`.
    df = _sp500_companies()
    tickers = df.loc[df["sector"] == sector, "ticker"].tolist()
    if not tickers:
        raise ValueError(f"No S&P‑500 tickers found for sector '{sector}'")

    records = []
    for tkr in tickers:
        info = yf.Ticker(tkr).info
        mc = info.get("marketCap")
        eps = info.get("trailingEps")
        sh = info.get("sharesOutstanding")
        if mc and eps and sh and eps != 0:
            net_income = eps * sh         # EPS * shares = trailing NI
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
