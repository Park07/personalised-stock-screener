import requests
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import io
import matplotlib.pyplot as plt
import base64
from fundamentals import get_fmp_valuation_data

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

def calculate_wacc(ticker, company_data):
    """Calculate Weighted Average Cost of Capital (WACC)"""
    
    # Get company profile data
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
        balance_url = f"{BASE_URL}balance-sheet-statement/{ticker}?5&apikey={FMP_API_KEY}"
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
    cash_flow_statements = get_cash_flow_statements(ticker, limit=10)
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
    discount_rate = calculate_wacc(ticker, company_data)
    
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
    
    return result

def generate_valuation_chart(ticker, valuation_data, dark_theme=True):
    """Generate a simplified intrinsic value chart similar to the provided example."""
    print(f"INFO: Generating simple valuation chart for {ticker}")
    
    try:
        # Try to get data from manual DCF calculation
            
                
        if not valuation_data:
            print(f"ERROR: Could not retrieve valuation data for {ticker}")
            return None
        
        # Extract valuation metrics
        company_name = valuation_data['company_name']
        current_price = valuation_data['current_price']
        fair_value = valuation_data['fair_value']
        
        # Determine if undervalued/overvalued and by how much
        if current_price > 0 and fair_value > 0:
            potential = ((fair_value / current_price) - 1) * 100
            is_undervalued = potential >= 0
        else:
            potential = 0
            is_undervalued = False
        
        # Setup colors
        if dark_theme:
            background_color = '#1a1a2e'
            text_color = 'white'
            secondary_text_color = '#a0a0b8'
            bar_color = '#4b6584'  # Blue-gray for value bar
        else:
            background_color = '#f8f9fa'
            text_color = '#333333'
            secondary_text_color = '#666666'
            bar_color = '#7f94b0'  # Lighter blue-gray
        
        # Set colors for valuation status
        if is_undervalued:
            valuation_color = '#00c853'  # Green for undervalued
            valuation_text = f"UNDERVALUATION {abs(potential):.0f}%"
        else:
            valuation_color = '#e53935'  # Red for overvalued
            valuation_text = f"OVERVALUATION {abs(potential):.0f}%"
        
        # Create figure
        fig = plt.figure(figsize=(10, 5), facecolor=background_color)
        
        # Setup grid for layout
        gs = plt.GridSpec(4, 12, figure=fig)
        
        # Title and logo area
        ax_title = fig.add_subplot(gs[0, :10])
        ax_title.axis('off')
        ax_title.text(0, 0.5, f"{ticker} Intrinsic Value", 
                     fontsize=24, fontweight='bold', color=text_color, ha='left', va='center')
        
        # Logo area (right side)
        ax_logo = fig.add_subplot(gs[0, 10:])
        ax_logo.axis('off')
        
        # Fair value display
        ax_value = fig.add_subplot(gs[1, :10])
        ax_value.axis('off')
        ax_value.text(0, 0.5, f"{fair_value:.2f}", 
                     fontsize=48, fontweight='bold', color='#7f94b0', ha='left', va='center')
        ax_value.text(len(f"{fair_value:.2f}") * 0.09, 0.5, " USD", 
                     fontsize=24, color=secondary_text_color, ha='left', va='center')
        
        # Valuation status box
        ax_status = fig.add_subplot(gs[1, 10:])
        ax_status.axis('off')
        rect = plt.Rectangle((0, 0.1), 1, 0.8, facecolor=valuation_color, alpha=1.0, edgecolor='none')
        ax_status.add_patch(rect)
        ax_status.text(0.5, 0.5, valuation_text, 
                      fontsize=12, fontweight='bold', color='white', ha='center', va='center')
        
        # Value and price bars
        ax_bars = fig.add_subplot(gs[2:, :])
        ax_bars.axis('off')
        
        # Calculate bar widths based on valuations
        total_width = 1.0
        
        if is_undervalued:
            # Intrinsic value > price
            value_width = total_width
            overvaluation_width = 0
            price_to_value_ratio = current_price / fair_value
            price_width = price_to_value_ratio * total_width
        else:
            # Intrinsic value < price
            value_width = fair_value / current_price * total_width
            overvaluation_width = total_width - value_width
            price_width = total_width
        
        # Value bar
        bar_height = 0.3
        bar_y = 0.6
        
        # Intrinsic value bar (blue-gray)
        value_bar = plt.Rectangle((0, bar_y), value_width, bar_height, 
                                 facecolor=bar_color, alpha=1.0, edgecolor='none')
        ax_bars.add_patch(value_bar)
        
        # Overvaluation extension (for overvalued stocks)
        if not is_undervalued:
            overval_bar = plt.Rectangle((value_width, bar_y), overvaluation_width, bar_height, 
                                       facecolor=valuation_color, alpha=0.5, edgecolor='none')
            ax_bars.add_patch(overval_bar)
        
        # Price bar (just outline)
        price_y = 0.25
        price_bar = plt.Rectangle((0, price_y), price_width, bar_height, 
                                 facecolor='none', edgecolor='#888888', linewidth=2)
        ax_bars.add_patch(price_bar)
        
        # Add labels
        ax_bars.text(0, bar_y + bar_height + 0.05, "Intrinsic Value", 
                    fontsize=12, color=text_color, ha='left', va='bottom')
        
        ax_bars.text(0, price_y + bar_height + 0.05, "Price", 
                    fontsize=12, color=text_color, ha='left', va='bottom')
        
        # Set axis limits
        ax_bars.set_xlim(0, 1.1)
        ax_bars.set_ylim(0, 1)
        
        plt.tight_layout()
        plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, facecolor=background_color, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to base64
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        print("INFO: Valuation chart generated successfully")
        return img_str
        
    except Exception as e:
        print(f"ERROR: Failed to generate valuation chart: {e}")
        return None