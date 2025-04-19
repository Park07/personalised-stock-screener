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
import matplotlib.image as mpimg
from urllib.request import urlopen
from PIL import Image

# Base URLs for API calls
BASE_URL = "https://financialmodelingprep.com/api/v3/"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"

from config import FMP_API_KEY

# Python logic all works but fmp free tier has restriction on how many requests
# (6 requests max for free tiers, and mine does 16)
# tried using cachinc but hits the limit even before reaching caching ;-;
# so hard coded the values after calculating
FAIR_VALUE_DATA = {
    'AAPL': {"fair_value": 141.52864356152915, "valuation_status": "Overvalued"},
    'NVDA': {"fair_value": 43.90598087684451, "valuation_status": "Overvalued"},
    'MSFT': {"fair_value": 250.68220502329478, "valuation_status": "Overvalued"},
    'TSLA': {"fair_value": 17.777165048414727, "valuation_status": "Overvalued"},
    'GOOG': {"fair_value": 134.10404691958382, "valuation_status": "Overvalued"},
    'SBUX': {"fair_value": 60.032336163203325, "valuation_status": "Overvalued"},
}

def get_current_price(ticker):
    """Get current price from FMP API"""
    try:
        # Get company profile
        profile_url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
        profile_response = requests.get(profile_url, timeout=10)
        profile_data = profile_response.json()
        
        if profile_data and len(profile_data) > 0:
            company_name = profile_data[0].get('companyName', ticker)
            current_price = profile_data[0].get('price', 0)
            return current_price, company_name
        
        return 0, ticker
    except Exception as e:
        print(f"Error fetching current price: {e}")
        return 0, ticker

def get_company_logo(ticker):
    """Get company logo URL"""
    try:
        # Most tech companies have recognizable logos we can use
        logo_map = {
            'AAPL': 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg',
            'MSFT': 'https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg',
            'GOOG': 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg',
            'NVDA': 'https://upload.wikimedia.org/wikipedia/commons/2/21/Nvidia_logo.svg',
            'TSLA': 'https://upload.wikimedia.org/wikipedia/commons/e/e8/Tesla_logo.png',
            'SBUX': 'https://upload.wikimedia.org/wikipedia/en/d/d3/Starbucks_Corporation_Logo_2011.svg',
        }
        
        return logo_map.get(ticker)
    except Exception as e:
        print(f"Error getting logo: {e}")
        return None

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
            print(f"No financial growth data for {ticker}")
            return None
        return data
    except Exception as e:
        print(f"Error fetching financial growth data: {e}")
        return None


def get_risk_free_rate():
    """Get 10‑year US Treasury Bond yield as risk‑free rate"""
    url = f"{BASE_URL}economic/treasury?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        for treasury in data:
            if treasury["maturity"] == "10 Years":
                return treasury["rate"] / 100
        return 0.0387
    except Exception as e:
        print(f"Error fetching treasury data: {e}")
        return 0.0387


def calculate_wacc(ticker):
    """Calculate Weighted Average Cost of Capital (WACC)"""
    company_data = get_company_data(ticker)
    if not company_data:
        return 0.09
    url = f"{BASE_URL}key-metrics/{ticker}?limit=1&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        metrics_data = response.json()
        if not metrics_data or len(metrics_data) == 0:
            return 0.09
        metrics = metrics_data[0]
        ratios_url = f"{BASE_URL}ratios/{ticker}?limit=1&apikey={FMP_API_KEY}"
        ratios_response = requests.get(ratios_url, timeout=10)
        ratios_data = ratios_response.json()
        if not ratios_data or len(ratios_data) == 0:
            return 0.09
        ratios = ratios_data[0]
        balance_url = f"{BASE_URL}balance-sheet-statement/{ticker}?limit=1&apikey={FMP_API_KEY}"
        balance_response = requests.get(balance_url, timeout=10)
        balance_data = balance_response.json()
        if not balance_data or len(balance_data) == 0:
            return 0.09
        balance = balance_data[0]
        risk_free_rate = get_risk_free_rate()
        beta = company_data.get("beta", 1.0)
        market_risk_premium = 0.04
        cost_of_equity = risk_free_rate + beta * market_risk_premium
        interest_expense = abs(metrics.get("interestExpense", 0))
        total_debt = balance.get("totalDebt", 0)
        if total_debt > 0 and interest_expense > 0:
            cost_of_debt = interest_expense / total_debt
        else:
            cost_of_debt = risk_free_rate + 0.02
        effective_tax_rate = ratios.get("effectiveTaxRate", 0.25)
        after_tax_cost_of_debt = cost_of_debt * (1 - effective_tax_rate)
        market_cap = company_data.get("mktCap", 0)
        enterprise_value = market_cap + total_debt
        if enterprise_value > 0:
            equity_weight = market_cap / enterprise_value
            debt_weight = total_debt / enterprise_value
        else:
            equity_weight, debt_weight = 0.7, 0.3
        wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_of_debt)
        return max(0.04, min(wacc, 0.15))
    except Exception as e:
        print(f"Error calculating WACC: {e}")
        return 0.09


def project_fcf(ticker, years=10):
    """Project Free Cash Flow for DCF calculation"""
    cash_flow_statements = get_cash_flow_statements(ticker, limit=5)
    if not cash_flow_statements:
        return None
    growth_data = get_financial_growth(ticker)
    historical_fcf = [
        stmt.get("freeCashFlow", 0) for stmt in cash_flow_statements if stmt.get("freeCashFlow", 0) != 0
    ]
    if not historical_fcf:
        print(f"No historical FCF data available for {ticker}")
        return None
    fcf_growth_rates = [(historical_fcf[i - 1] / historical_fcf[i]) - 1 for i in range(1, len(historical_fcf))]
    if fcf_growth_rates:
        historical_growth_rate = np.median(fcf_growth_rates)
    else:
        historical_growth_rate = (
            growth_data[0].get("freeCashFlowGrowth", 0.05) if growth_data else 0.05
        )
    historical_growth_rate = max(-0.20, min(historical_growth_rate, 0.25))
    latest_fcf = historical_fcf[0]
    projected_fcf = [latest_fcf * (1 + historical_growth_rate) ** i for i in range(1, 6)]
    terminal_growth_rate = 0.027
    for i in range(6, years + 1):
        stage = i - 5
        transition_weight = stage / 5
        current_growth = historical_growth_rate * (1 - transition_weight) + terminal_growth_rate * transition_weight
        projected_fcf.append(latest_fcf * (1 + current_growth) ** i)
    return {
        "latest_fcf": latest_fcf,
        "historical_growth_rate": historical_growth_rate,
        "terminal_growth_rate": terminal_growth_rate,
        "projected_fcf": projected_fcf,
    }


def calculate_dcf_valuation(ticker):
    """Calculate DCF valuation for a stock"""
    print(f"Calculating DCF valuation for {ticker}...")
    company_data = get_company_data(ticker)
    if not company_data:
        return None
    fcf_projections = project_fcf(ticker)
    if not fcf_projections:
        return None
    discount_rate = calculate_wacc(ticker)
    projected_fcf = fcf_projections["projected_fcf"]
    terminal_growth_rate = fcf_projections["terminal_growth_rate"]
    pv_fcf = [fcf / ((1 + discount_rate) ** (i + 1)) for i, fcf in enumerate(projected_fcf)]
    terminal_fcf = projected_fcf[-1] * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
    pv_terminal_value = terminal_value / ((1 + discount_rate) ** len(projected_fcf))
    enterprise_value = sum(pv_fcf) + pv_terminal_value
    net_debt = 0
    try:
        balance_sheet_url = f"{BASE_URL}balance-sheet-statement/{ticker}?limit=1&apikey={FMP_API_KEY}"
        balance_response = requests.get(balance_sheet_url, timeout=10)
        balance_data = balance_response.json()
        if balance_data and len(balance_data) > 0:
            total_debt = balance_data[0].get("totalDebt", 0)
            cash_eq = balance_data[0].get("cashAndCashEquivalents", 0)
            sti = balance_data[0].get("shortTermInvestments", 0)
            net_debt = total_debt - (cash_eq + sti)
    except Exception as e:
        print(f"Error fetching balance sheet: {e}")
    equity_value = enterprise_value - net_debt
    shares_outstanding = company_data.get("sharesOutstanding", 0)
    if shares_outstanding <= 0:
        market_cap = company_data.get("mktCap", 0)
        current_price = company_data.get("price", 0)
        if market_cap > 0 and current_price > 0:
            shares_outstanding = market_cap / current_price
        else:
            print(f"Unable to determine shares outstanding for {ticker}")
            return None
    fair_value_per_share = equity_value / shares_outstanding
    current_price = company_data.get("price", 0)
    if current_price > 0:
        potential = ((fair_value_per_share / current_price) - 1) * 100
        valuation_status = "Undervalued" if potential >= 0 else "Overvalued"
    else:
        potential, valuation_status = 0, "Unknown"
    return {
        "ticker": ticker,
        "company_name": company_data.get("companyName", ticker),
        "current_price": current_price,
        "fair_value": fair_value_per_share,
        "potential": potential,
        "valuation_status": valuation_status,
        "market_cap": company_data.get("mktCap", 0),
        "shares_outstanding": shares_outstanding,
        "wacc": discount_rate,
        "historical_growth_rate": fcf_projections["historical_growth_rate"],
        "terminal_growth_rate": terminal_growth_rate,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "calculation_date": datetime.now().strftime("%Y-%m-%d"),
    }

def generate_enhanced_valuation_chart(ticker, dark_theme=True):
    """Generate an enhanced valuation chart with bright colors and company logo"""
    print(f"INFO: Generating enhanced valuation chart for {ticker}")
    
    try:
        # Get current price and company name
        current_price, company_name = get_current_price(ticker)
        
        # Get fair value from our store
        ticker = ticker.upper()
        if ticker in FAIR_VALUE_DATA:
            fair_value = FAIR_VALUE_DATA[ticker]["fair_value"]
        else:
            print(f"No fair value data for {ticker}")
            return None
        
        # Calculate valuation percentage
        if current_price > 0 and fair_value > 0:
            potential = ((fair_value / current_price) - 1) * 100
            is_undervalued = potential >= 0
            valuation_percentage = abs(potential)
            valuation_status = "Undervalued" if is_undervalued else "Overvalued"
        else:
            potential = 0
            is_undervalued = False
            valuation_percentage = 0
            valuation_status = "Unknown"
        
        # Setup colors - bright neon theme
        background_color = '#161629'  # Dark blue background
        text_color = 'white'
        secondary_text_color = '#a0a0b8'
        
        # Neon colors
        if is_undervalued:
            valuation_color = '#00ff9d'  # Bright neon green
            value_bar_color = '#34d399'  # Teal for value bar
        else:
            valuation_color = '#ff3467'  # Bright neon pink/red
            value_bar_color = '#6366f1'  # Indigo for value bar
        
        # Create figure
        fig = plt.figure(figsize=(10, 6), facecolor=background_color)
        
        # Setup grid for layout - adjust to make room for logo
        gs = plt.GridSpec(6, 12, figure=fig)
        
        # Title area
        ax_title = fig.add_subplot(gs[0:1, :8])
        ax_title.axis('off')
        ax_title.text(0, 0.5, f"{ticker} Intrinsic Value", 
                     fontsize=24, fontweight='bold', color=text_color, ha='left', va='center')
        
        # Company logo area
        ax_logo = fig.add_subplot(gs[0:2, 9:])
        ax_logo.axis('off')
        
        # Try to add a company logo if available
        logo_url = get_company_logo(ticker)
        if logo_url:
            try:

                
                # Use a basic logo if available
                with urlopen(logo_url) as url:
                    if logo_url.endswith('.svg'):
                        # Handle SVG differently
                        try:
                            from io import BytesIO
                            import cairosvg
                            
                            png_data = cairosvg.svg2png(url=logo_url)
                            img = Image.open(BytesIO(png_data))
                            ax_logo.imshow(img)
                        except ImportError:
                            # Just draw a placeholder if cairosvg not available
                            circle = plt.Circle((0.5, 0.5), 0.4, fc='white')
                            ax_logo.add_patch(circle)
                            ax_logo.text(0.5, 0.5, ticker, ha='center', va='center', 
                                        fontsize=20, fontweight='bold', color='black')
                    else:
                        img = mpimg.imread(url, format='png')
                        ax_logo.imshow(img)
                        
            except Exception as e:
                print(f"Error loading logo: {e}")
                # Fallback - draw a simple placeholder
                circle = plt.Circle((0.5, 0.5), 0.4, fc='white')
                ax_logo.add_patch(circle)
                ax_logo.text(0.5, 0.5, ticker, ha='center', va='center', 
                           fontsize=20, fontweight='bold', color='black')
        
        # Fair value display
        ax_value = fig.add_subplot(gs[1:3, :6])
        ax_value.axis('off')
        ax_value.text(0, 0.5, f"{fair_value:.2f}", 
                     fontsize=48, fontweight='bold', color='#9ca3af', ha='left', va='center')
        ax_value.text(len(f"{fair_value:.2f}") * 0.059, 0.5, " USD", 
                     fontsize=24, color=secondary_text_color, ha='left', va='center')
        
        # Valuation status box
        ax_status = fig.add_subplot(gs[1:2, 7:9])
        ax_status.axis('off')
        rect = plt.Rectangle((0, 0.1), 1, 0.8, facecolor=valuation_color, alpha=1.0, edgecolor='none')
        ax_status.add_patch(rect)
        ax_status.text(0.5, 0.5, f"{valuation_status.upper()} {valuation_percentage:.0f}%", 
                      fontsize=10, fontweight='bold', color='white', ha='center', va='center')
        
        # Value and price bars
        ax_bars = fig.add_subplot(gs[3:, :])
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
        
        # Intrinsic value bar
        value_bar = plt.Rectangle((0, bar_y), value_width, bar_height, 
                                 facecolor=value_bar_color, alpha=1.0, edgecolor='none')
        ax_bars.add_patch(value_bar)
        
        # Overvaluation extension (for overvalued stocks)
        if not is_undervalued:
            overval_bar = plt.Rectangle((value_width, bar_y), overvaluation_width, bar_height, 
                                       facecolor=valuation_color, alpha=0.5, edgecolor='none')
            ax_bars.add_patch(overval_bar)
        
        # Price bar (just outline with glow effect for neon look)
        price_y = 0.25
        edge_color = '#ffffff'
        linewidth = 2
        
        # Create a subtle glow effect
        for i in range(3):
            alpha = 0.1 - i * 0.03
            lw = linewidth + i * 1
            price_bar_glow = plt.Rectangle((0, price_y), price_width, bar_height, 
                                         facecolor='none', edgecolor=edge_color, 
                                         linewidth=lw, alpha=alpha)
            ax_bars.add_patch(price_bar_glow)
        
        # Actual price bar
        price_bar = plt.Rectangle((0, price_y), price_width, bar_height, 
                                 facecolor='none', edgecolor=edge_color, linewidth=linewidth)
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
        
        # Add valuation date
        ax_bars.text(1.0, 0.05, f"Calculated: {datetime.now().strftime('%Y-%m-%d')}", 
                    fontsize=8, ha='right', va='bottom', color='#6b7280')
        
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