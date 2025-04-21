import requests
import numpy as np
from functools import lru_cache
from profiles import get_profile_metrics
from company_data import FAIR_VALUE_DATA, STOCK_UNIVERSE, SECTORS
from cache_utils import get_cached_data, cache_data
from config import FMP_API_KEY

# Base URL for API
BASE_URL = "https://financialmodelingprep.com/api/v3/"

@lru_cache(maxsize=100)
def get_company_profile(ticker):
    """Get company profile with caching to reduce API calls"""
    cache_key = f"profile_{ticker}"
    cached = get_cached_data(cache_key, 86400)  # 24 hour cache
    if cached:
        return cached
    
    try:
        url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if not data or len(data) == 0:
            return None
            
        profile = data[0]
        cache_data(cache_key, profile)
        return profile
    except Exception as e:
        print(f"Error fetching profile for {ticker}: {e}")
        return None

@lru_cache(maxsize=100)
def get_ratios_ttm(ticker):
    """Get financial ratios TTM with caching"""
    cache_key = f"ratios_ttm_{ticker}"
    cached = get_cached_data(cache_key, 86400)  # 24 hour cache
    if cached:
        return cached
    
    try:
        url = f"{BASE_URL}ratios-ttm/{ticker}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {}
            
        data = response.json()
        if not data or len(data) == 0:
            return {}
            
        ratios = data[0]
        cache_data(cache_key, ratios)
        return ratios
    except Exception as e:
        print(f"Error fetching ratios for {ticker}: {e}")
        return {}

@lru_cache(maxsize=100)
def get_growth_data(ticker):
    """Get financial growth data with caching"""
    cache_key = f"growth_{ticker}"
    cached = get_cached_data(cache_key, 86400)  # 24 hour cache
    if cached:
        return cached
    
    
    growth_estimates = {

    }
    

    result = growth_estimates.get(ticker, {'revenue_growth': 0.05, 'earnings_growth': 0.05})
    cache_data(cache_key, result)
    return result

def get_company_metrics(ticker):
    """Get all necessary metrics for a company"""
    cache_key = f"metrics_{ticker}"
    cached = get_cached_data(cache_key, 3600)  # 1 hour cache
    if cached:
        return cached
    
    try:
        # Get basic profile
        profile = get_company_profile(ticker)
        if not profile:
            return None
        
        # getting ratios
        ratios = get_ratios_ttm(ticker)

        # growth
        growth = get_growth_data(ticker)


        fair_value = FAIR_VALUE_DATA.get(ticker, {}).get('fair_value', 0)
        valuation_status = FAIR_VALUE_DATA.get(ticker, {}).get('valuation_status', 'Unknown')

        current_price = profile.get('price', 0)
        price_to_intrinsic = current_price / fair_value if fair_value > 0 else 1

        # Compile all metrics
        metrics = {
            'ticker': ticker,
            'name': profile.get('companyName', ticker),
            'sector': profile.get('sector', ''),
            'industry': profile.get('industry', ''),
            'market_cap': profile.get('mktCap', 0),
            'current_price': current_price,
            'fair_value': fair_value,
            'valuation_status': valuation_status,
            'price_to_intrinsic': price_to_intrinsic,
            
            # From ratios
            'pe_ratio': ratios.get('peRatioTTM', 0),
            'dividend_yield': ratios.get('dividendYielTTM', profile.get('lastDiv', 0) / current_price if current_price > 0 else 0),
            'payout_ratio': ratios.get('payoutRatioTTM', 0),
            'debt_to_equity': ratios.get('debtEquityRatioTTM', 0),
            'return_on_equity': ratios.get('returnOnEquityTTM', 0),
            'return_on_assets': ratios.get('returnOnAssetsTTM', 0),
            'free_cash_flow_yield': ratios.get('freeCashFlowYieldTTM', 0),
            
            # From growth
            'revenue_growth': growth.get('revenue_growth', 0),
            'earnings_growth': growth.get('earnings_growth', 0)
        }
        
        cache_data(cache_key, metrics)
        return metrics
    except Exception as e:
        print(f"Error getting metrics for {ticker}: {e}")
        return None

def normalise_metric(value, all_values, higher_better=True):
    """Normalise a metric value between 0 and 1"""
    if not all_values or len(all_values) <= 1:
        return 0.5
    
    # Remove any None values
    all_values = [v for v in all_values if v is not None]
    
    # If still no valid values, return middle score
    if not all_values:
        return 0.5
    
    min_val, max_val = min(all_values), max(all_values)
    
    # If all values are the same, return middle score
    if min_val == max_val:
        return 0.5
    
    # Normalise value
    normalised = (value - min_val) / (max_val - min_val)
    
    # Invert if lower is better
    if not higher_better:
        normalised = 1 - normalised
    
    return normalised

def generate_insight(metric, value, normalised_score, profile_metrics):
    """Generate human-readable insight for a metric"""
    if normalised_score >= 0.7:
        category = "strength"
    elif normalised_score <= 0.3:
        category = "caution"
    else:
        category = "neutral"
    
    # Format the message based on metric type
    if metric == 'pe_ratio':
        message = f"P/E ratio: {value:.1f}x"
        if category == "strength":
            message += " (attractively valued)"
        elif category == "caution":
            message += " (relatively expensive)"
    elif metric == 'revenue_growth':
        message = f"Revenue growth: {value*100:.1f}%"
        if category == "strength":
            message += " (strong growth)"
        elif category == "caution":
            message += " (weak growth)"
    elif metric == 'earnings_growth':
        message = f"Earnings growth: {value*100:.1f}%"
        if category == "strength":
            message += " (strong profitability trend)"
        elif category == "caution":
            message += " (weak profitability trend)"
    elif metric == 'dividend_yield':
        message = f"Dividend yield: {value*100:.1f}%"
        if category == "strength":
            message += " (attractive income)"
        elif category == "caution":
            message += " (low income)"
    elif metric == 'debt_to_equity':
        message = f"Debt-to-equity: {value:.2f}"
        if category == "strength":
            message += " (strong balance sheet)"
        elif category == "caution":
            message += " (high leverage)"
    elif metric == 'return_on_equity':
        message = f"Return on equity: {value*100:.1f}%"
        if category == "strength":
            message += " (efficient capital use)"
        elif category == "caution":
            message += " (poor capital efficiency)"
    elif metric == 'return_on_assets':
        message = f"Return on assets: {value*100:.1f}%"
        if category == "strength":
            message += " (efficient asset use)"
        elif category == "caution":
            message += " (poor asset efficiency)"
    elif metric == 'free_cash_flow_yield':
        message = f"Free cash flow yield: {value*100:.1f}%"
        if category == "strength":
            message += " (strong cash generation)"
        elif category == "caution":
            message += " (weak cash generation)"
    elif metric == 'price_to_intrinsic':
        if value < 0.8:
            message = f"Trading at {(1-value)*100:.1f}% below intrinsic value"
            category = "strength"
        elif value > 1.2:
            message = f"Trading at {(value-1)*100:.1f}% above intrinsic value"
            category = "caution"
        else:
            message = f"Trading near intrinsic value"
            category = "neutral"
    elif metric == 'market_cap':
        message = f"Market cap: ${value/1e9:.1f}B"
        if category == "strength":
            message += " (large, stable company)"
        elif category == "caution":
            message += " (smaller company)"
    else:
        message = f"{metric.replace('_', ' ').title()}: {value}"
    
    return {
        "metric": metric,
        "value": value,
        "category": category,
        "message": message,
        "importance": profile_metrics.get(metric, {}).get('weight', 0)
    }

def rank_companies(goal, risk, sector=None):
    """Rank companies based on investment goal and risk tolerance"""
    cache_key = f"rank_{goal}_{risk}_{sector}"
    cached = get_cached_data(cache_key, 3600)  # 1 hour cache
    if cached:
        return cached
        
    # Get metrics for the investment profile
    profile_metrics = get_profile_metrics(goal, risk)
    
    # Filter universe by sector if specified
    if sector:
        universe = SECTORS.get(sector, [])
    else:
        universe = STOCK_UNIVERSE
    
    # Get metrics for all companies in universe
    company_metrics = {}
    for ticker in universe:
        metrics = get_company_metrics(ticker)
        if metrics:
            company_metrics[ticker] = metrics
    
    # Collect values for each metric for normalisation
    metric_values = {}
    for metric in profile_metrics:
        metric_values[metric] = [
            metrics.get(metric)
            for metrics in company_metrics.values()
            if metrics.get(metric) is not None
        ]
    
    # Calculate score for each company
    ranked_companies = []
    
    for ticker, metrics in company_metrics.items():
        score = 0
        insights = []
        
        for metric, config in profile_metrics.items():
            value = metrics.get(metric)
            if value is None:
                continue
            
            # Normalize score
            normalised = normalise_metric(
                value,
                metric_values[metric],
                config['higher_better']
            )
            
            # Add to total score, weighted by importance
            score += normalised * config['weight']
            
            # Generate insight
            insights.append(generate_insight(metric, value, normalised, profile_metrics))
        
        # Convert score to 0-100 scale
        score = score * 100
        
        # Split insights into strengths and cautions
        strengths = [i for i in insights if i['category'] == 'strength']
        cautions = [i for i in insights if i['category'] == 'caution']
        
        # Sort by importance
        strengths.sort(key=lambda x: x['importance'], reverse=True)
        cautions.sort(key=lambda x: x['importance'], reverse=True)
        
        # Keep top 3 strengths and top 2 cautions
        strengths = strengths[:3]
        cautions = cautions[:2]
        
        ranked_companies.append({
            'ticker': ticker,
            'name': metrics.get('name', ticker),
            'score': score,
            'sector': metrics.get('sector', ''),
            'market_cap': metrics.get('market_cap', 0),
            'current_price': metrics.get('current_price', 0),
            'pe_ratio': metrics.get('pe_ratio', 0),
            'dividend_yield': metrics.get('dividend_yield', 0),
            'strengths': strengths,
            'cautions': cautions,
            'metrics': metrics  # Keep all metrics for parallel chart
        })
    
    # Sort by score
    ranked_companies.sort(key=lambda x: x['score'], reverse=True)
    
    # Cache results
    cache_data(cache_key, ranked_companies)
    
    return ranked_companies