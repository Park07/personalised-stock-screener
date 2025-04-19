import requests
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# Base URLs for API calls
BASE_URL = "https://financialmodelingprep.com/api/v3/"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"


from config import FMP_API_KEY


def get_company_data(ticker):
    """Get company profile data"""

    url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data or len(data) == 0:
            print(f"No company data found for {ticker}")
            return None
            
        return data[0]
    except Exception as e:
        print(f"Error fetching company data: {e}")
        return None

def get_cash_flow_statements(ticker, period="annual", limit=10):
    """Get cash flow statement data"""
    
    url = f"{BASE_URL}cash-flow-statement/{ticker}?period={period}&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if not data or len(data) == 0:
            print(f"No cash flow data found for {ticker}")
            return None
            
        return data
    except Exception as e:
        print(f"Error fetching cash flow data: {e}")
        return None

def get_financial_growth(ticker, period="annual"):
    """Get financial growth rates"""
    
    url = f"{BASE_URL}financial-growth/{ticker}?period={period}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data or len(data) == 0:
            print(f"No financial growth data found for {ticker}")
            return None
            
        return data
    except Exception as e:
        print(f"Error fetching financial growth data: {e}")
        return None

def get_risk_free_rate():
    """Get 10-year US Treasury Bond yield as risk-free rate"""
    
    url = f"{BASE_URL}economic/treasury?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Find 10-year treasury yield
        for treasury in data:
            if treasury['maturity'] == '10 Years':
                return treasury['rate'] / 100  # Convert percentage to decimal
        
        return 0.0387  # Default if not found
    except Exception as e:
        print(f"Error fetching treasury data: {e}")
        return 0.0387  # Default value

def calculate_wacc(ticker):
    """Calculate Weighted Average Cost of Capital (WACC)"""
    
    # Get company profile data
    company_data = get_company_data(ticker)
    if not company_data:
        return 0.09
    
    # Get key metrics
    url = f"{BASE_URL}key-metrics/{ticker}?limit=1&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        metrics_data = response.json()
        
        if not metrics_data or len(metrics_data) == 0:
            return 0.09
            
        metrics = metrics_data[0]
        
        # Get financial ratios
        ratios_url = f"{BASE_URL}ratios/{ticker}?limit=1&apikey={FMP_API_KEY}"
        ratios_response = requests.get(ratios_url, timeout=10)
        ratios_data = ratios_response.json()
        
        if not ratios_data or len(ratios_data) == 0:
            return 0.09
            
        ratios = ratios_data[0]
        
        # Get balance sheet
        balance_url = f"{BASE_URL}balance-sheet-statement/{ticker}?limit=1&apikey={FMP_API_KEY}"
        balance_response = requests.get(balance_url, timeout=10)
        balance_data = balance_response.json()
        
        if not balance_data or len(balance_data) == 0:
            return 0.09
            
        balance = balance_data[0]
        
        # Calculate WACC components
        
        # 1. Cost of Equity (using CAPM)
        risk_free_rate = get_risk_free_rate()
        beta = company_data.get('beta', 1.0)
        market_risk_premium = 0.05  # Assumed market risk premium of 5%
        
        cost_of_equity = risk_free_rate + beta * market_risk_premium
        
        # 2. Cost of Debt
        interest_expense = abs(metrics.get('interestExpense', 0))
        total_debt = balance.get('totalDebt', 0)
        
        if total_debt > 0 and interest_expense > 0:
            cost_of_debt = interest_expense / total_debt
        else:
            cost_of_debt = risk_free_rate + 0.02  # Default: risk-free rate + 2%
        
        # Apply tax shield to cost of debt
        effective_tax_rate = ratios.get('effectiveTaxRate', 0.25)
        after_tax_cost_of_debt = cost_of_debt * (1 - effective_tax_rate)
        
        # 3. Capital structure weights
        market_cap = company_data.get('mktCap', 0)
        enterprise_value = market_cap + total_debt
        
        if enterprise_value > 0:
            equity_weight = market_cap / enterprise_value
            debt_weight = total_debt / enterprise_value
        else:
            equity_weight = 0.7  # Default: 70% equity
            debt_weight = 0.3    # Default: 30% debt
        
        # Calculate WACC
        wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_of_debt)
        
        # Ensure reasonable bounds
        wacc = max(0.05, min(wacc, 0.15))
        
        return wacc
        
    except Exception as e:
        print(f"Error calculating WACC: {e}")
        return 0.09  # Default to 9%

def project_fcf(ticker, years=10):
    """Project Free Cash Flow for DCF calculation"""
    # Get historical cash flow data
    cash_flow_statements = get_cash_flow_statements(ticker, limit=5)
    if not cash_flow_statements:
        return None
    
    # Get growth rates
    growth_data = get_financial_growth(ticker)
    
    # Extract free cash flow values
    historical_fcf = []
    
    for statement in cash_flow_statements:
        fcf = statement.get('freeCashFlow', 0)
        if fcf != 0:
            historical_fcf.append(fcf)
    
    if len(historical_fcf) == 0:
        print(f"No historical FCF data available for {ticker}")
        return None
    
    # Calculate historical FCF growth rate
    fcf_growth_rates = []
    for i in range(1, len(historical_fcf)):
        growth_rate = (historical_fcf[i-1] / historical_fcf[i]) - 1
        fcf_growth_rates.append(growth_rate)
    
    # Use median of historical growth rates to avoid outliers
    if len(fcf_growth_rates) > 0:
        historical_growth_rate = np.median(fcf_growth_rates)
    else:
        # If no historical growth data, use recent FCF growth from API or default
        if growth_data and len(growth_data) > 0:
            historical_growth_rate = growth_data[0].get('freeCashFlowGrowth', 0.05)
        else:
            historical_growth_rate = 0.05
    
    # Ensure growth rate is within reasonable bounds
    historical_growth_rate = max(-0.20, min(historical_growth_rate, 0.25))
    
    # Get latest FCF as starting point
    latest_fcf = historical_fcf[0]
    
    # Project FCF for future years - two-stage model
    projected_fcf = []
    
    # First 5 years: Higher growth phase
    growth_rate = historical_growth_rate
    for i in range(1, 6):
        fcf = latest_fcf * (1 + growth_rate) ** i
        projected_fcf.append(fcf)
    
    # Next 5 years: Transition to terminal growth
    terminal_growth_rate = 0.025  # Long-term growth assumption (2.5%)
    for i in range(6, years + 1):
        # Linear decline in growth rate
        stage = i - 5
        transition_weight = stage / 5
        current_growth = growth_rate * (1 - transition_weight) + terminal_growth_rate * transition_weight
        fcf = latest_fcf * (1 + current_growth) ** i
        projected_fcf.append(fcf)
    
    return {
        'latest_fcf': latest_fcf,
        'historical_growth_rate': historical_growth_rate,
        'terminal_growth_rate': terminal_growth_rate,
        'projected_fcf': projected_fcf
    }

def calculate_dcf_valuation(ticker):
    """Calculate DCF valuation for a stock"""
    print(f"Calculating DCF valuation for {ticker}...")
    
    # Get company data
    company_data = get_company_data(ticker)
    if not company_data:
        return None
    
    # Get projected FCF
    fcf_projections = project_fcf(ticker)
    if not fcf_projections:
        return None
    
    # Get discount rate (WACC)
    discount_rate = calculate_wacc(ticker)
    
    # Calculate present value of projected cash flows
    projected_fcf = fcf_projections['projected_fcf']
    terminal_growth_rate = fcf_projections['terminal_growth_rate']
    
    pv_fcf = []
    for i, fcf in enumerate(projected_fcf):
        year = i + 1
        pv = fcf / ((1 + discount_rate) ** year)
        pv_fcf.append(pv)
    
    # Calculate terminal value using Gordon Growth Model
    terminal_fcf = projected_fcf[-1] * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
    
    # Discount terminal value
    pv_terminal_value = terminal_value / ((1 + discount_rate) ** len(projected_fcf))
    
    # Sum present values for enterprise value
    enterprise_value = sum(pv_fcf) + pv_terminal_value
    
    # Get current net debt
    net_debt = 0
    try:
        balance_sheet_url = f"{BASE_URL}balance-sheet-statement/{ticker}?limit=1&apikey={FMP_API_KEY}"
        balance_response = requests.get(balance_sheet_url, timeout=10)
        balance_data = balance_response.json()
        
        if balance_data and len(balance_data) > 0:
            total_debt = balance_data[0].get('totalDebt', 0)
            cash_and_equivalents = balance_data[0].get('cashAndCashEquivalents', 0)
            short_term_investments = balance_data[0].get('shortTermInvestments', 0)
            
            net_debt = total_debt - (cash_and_equivalents + short_term_investments)
    except Exception as e:
        print(f"Error fetching balance sheet: {e}")
    
    # Calculate equity value
    equity_value = enterprise_value - net_debt
    
    # Calculate per-share value
    shares_outstanding = company_data.get('sharesOutstanding', 0)
    if shares_outstanding <= 0:
        # Try to estimate from market cap
        market_cap = company_data.get('mktCap', 0)
        current_price = company_data.get('price', 0)
        
        if market_cap > 0 and current_price > 0:
            shares_outstanding = market_cap / current_price
        else:
            print(f"Unable to determine shares outstanding for {ticker}")
            return None
    
    fair_value_per_share = equity_value / shares_outstanding
    current_price = company_data.get('price', 0)
    
    # Determine if undervalued/overvalued
    if current_price > 0:
        potential = ((fair_value_per_share / current_price) - 1) * 100
        valuation_status = "Undervalued" if potential >= 0 else "Overvalued"
    else:
        potential = 0
        valuation_status = "Unknown"
    
    # Format results
    result = {
        'ticker': ticker,
        'company_name': company_data.get('companyName', ticker),
        'current_price': current_price,
        'fair_value': fair_value_per_share,
        'potential': potential,
        'valuation_status': valuation_status,
        'market_cap': company_data.get('mktCap', 0),
        'shares_outstanding': shares_outstanding,
        'wacc': discount_rate,
        'historical_growth_rate': fcf_projections['historical_growth_rate'],
        'terminal_growth_rate': terminal_growth_rate,
        'enterprise_value': enterprise_value,
        'equity_value': equity_value,
        'calculation_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    return results


