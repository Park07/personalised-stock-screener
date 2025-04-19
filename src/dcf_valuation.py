from fundamentals import get_fmp_valuation_data
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import matplotlib.colors as mc
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import requests
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
import colorsys

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

def lighten_color(color, factor=0.3):
    """Create a lighter version of a color"""
    if isinstance(color, str) and color.startswith('#'):
        r = int(color[1:3], 16) / 255.0
        g = int(color[3:5], 16) / 255.0
        b = int(color[5:7], 16) / 255.0
        
        r = min(1.0, r + (1 - r) * factor)
        g = min(1.0, g + (1 - g) * factor)
        b = min(1.0, b + (1 - b) * factor)
        
        return (r, g, b)
    return color

def adjust_lightness(color, amount=0.5):
    """Lightens or darkens a color"""
    try:
        c = mc.cnames[color] if color in mc.cnames else color
        c = colorsys.rgb_to_hls(*mc.to_rgb(c))
        adjusted_lightness = max(0, min(1, amount * c[1]))
        return colorsys.hls_to_rgb(c[0], adjusted_lightness, c[2])
    except Exception:
        if isinstance(color, str):
            return mc.to_rgb(color)
        return color

def generate_premium_valuation_chart(ticker, dark_theme=True):
    """Generate a premium financial chart comparing intrinsic value to current price"""
    ticker = ticker.upper()
    
    # Get data using your original functions
    current_price, company_name = get_current_price(ticker)
    fair_value = FAIR_VALUE_DATA.get(ticker, {}).get("fair_value", 0)
    
    # Calculate metrics
    diff = fair_value - current_price
    diff_pct = (diff / current_price * 100) if current_price > 0 else 0
    is_undervalued = diff > 0
    
    # Color schemes - premium financial aesthetics
    if dark_theme:
        bg_color = '#131722'  # TradingView-like dark blue
        text_color = '#FFFFFF'
        subtext_color = '#9FABB6'
        undervalued_color = '#4CAF50'  # Green
        overvalued_color = '#F44336'  # Red
        price_color = '#2196F3'  # Blue
        value_color = '#FFC107'  # Amber
        card_bg = '#1E222D'  # Slightly lighter card background
        border_color = '#2A2E39'  # Border color for cards
        grid_color = '#363C4E'
    else:
        bg_color = '#FFFFFF'
        text_color = '#253248'
        subtext_color = '#66728C'
        undervalued_color = '#4CAF50'  # Green
        overvalued_color = '#F44336'  # Red
        price_color = '#2196F3'  # Blue
        value_color = '#673AB7'  # Deep Purple
        card_bg = '#F3F6F9'  # Light gray card background
        border_color = '#E5E8F0'  # Light gray borders
        grid_color = '#E2E8F0'
    
    # Valuation styling
    valuation_color = undervalued_color if is_undervalued else overvalued_color
    status_text = "UNDERVALUED" if is_undervalued else "OVERVALUED"
    sign = "+" if is_undervalued else ""
    
    # Create the figure with high DPI for crisp rendering
    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 10})
    fig = plt.figure(figsize=(12, 6.75), dpi=120)
    fig.patch.set_facecolor(bg_color)
    
    # Define grid layout
    gs = fig.add_gridspec(12, 24, wspace=0.1, hspace=0.6)
    
    # Header with company info and logo
    header_ax = fig.add_subplot(gs[0:2, 0:18])
    header_ax.axis('off')
    header_ax.set_facecolor(bg_color)
    
    # Title with styling
    title = header_ax.text(0.01, 0.65, f"{ticker}", 
                         fontsize=26, fontweight='bold', color=text_color)
    title.set_path_effects([
        path_effects.withStroke(linewidth=2, foreground=valuation_color, alpha=0.2)
    ])
    
    # Subtitle with company name
    header_ax.text(0.01, 0.3, f"{company_name}", 
                 fontsize=16, color=subtext_color)
    
    # Valuation difference
    header_ax.text(0.01, 0.0, f"{sign}${abs(diff):.2f} ({sign}{abs(diff_pct):.1f}%)", 
                 fontsize=18, fontweight='bold', color=valuation_color)
    
    # Logo section
    logo_ax = fig.add_subplot(gs[0:2, 18:24])
    logo_ax.axis('off')
    logo_ax.set_facecolor(bg_color)
    
    # Try to fetch and display logo
    logo_url = get_company_logo(ticker)
    if logo_url:
        try:
            response = requests.get(logo_url, timeout=5)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                # For SVG images, convert to RGB mode
                if img.mode == 'RGBA':
                    white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    white_bg.paste(img, (0, 0), img)
                    img = white_bg.convert('RGB')
                
                logo_ax.imshow(img)
                logo_ax.set_aspect('equal')
        except Exception as e:
            print(f"Error displaying logo: {e}")
    
    # Valuation badge
    badge_ax = fig.add_subplot(gs[2:4, 18:24])
    badge_ax.axis('off')
    badge_ax.set_facecolor(bg_color)
    
    # Create a rounded rectangle for the badge
    badge = mpatches.Rectangle((0.05, 0.15), 0.9, 0.7, 
                             facecolor=valuation_color, alpha=0.85, 
                             edgecolor='none')
    badge_ax.add_patch(badge)
    
    # Badge text
    badge_ax.text(0.5, 0.5, f"{status_text} {abs(diff_pct):.1f}%", 
                fontsize=14, fontweight='bold', color='white',
                ha='center', va='center')
    
    # Value card
    value_card = fig.add_subplot(gs[2:6, 0:11])
    value_card.axis('off')
    value_card.set_facecolor(bg_color)
    
    # Card background
    card_patch = mpatches.Rectangle((0.02, 0.02), 0.96, 0.96, 
                                   facecolor=card_bg, alpha=1.0,
                                   edgecolor=border_color, linewidth=1)
    value_card.add_patch(card_patch)
    
    # Intrinsic Value Label
    value_card.text(0.5, 0.85, "INTRINSIC VALUE", 
                  fontsize=12, fontweight='bold', color=subtext_color,
                  ha='center', va='center')
    
    # Intrinsic Value Number
    value_text = value_card.text(0.5, 0.5, f"${fair_value:.2f}", 
                               fontsize=24, fontweight='bold', color=value_color,
                               ha='center', va='center')
    value_text.set_path_effects([
        path_effects.withStroke(linewidth=3, foreground=value_color, alpha=0.2)
    ])
    
    # Context
    value_context = "ABOVE MARKET" if is_undervalued else "BELOW MARKET"
    value_card.text(0.5, 0.2, value_context, 
                  fontsize=11, color=subtext_color,
                  ha='center', va='center')
    
    # Price card
    price_card = fig.add_subplot(gs[2:6, 12:18])
    price_card.axis('off')
    price_card.set_facecolor(bg_color)
    
    # Card background
    card_patch = mpatches.Rectangle((0.02, 0.02), 0.96, 0.96, 
                                   facecolor=card_bg, alpha=1.0,
                                   edgecolor=border_color, linewidth=1)
    price_card.add_patch(card_patch)
    
    # Current Price Label
    price_card.text(0.5, 0.85, "CURRENT PRICE", 
                  fontsize=12, fontweight='bold', color=subtext_color,
                  ha='center', va='center')
    
    # Current Price Number
    price_text = price_card.text(0.5, 0.5, f"${current_price:.2f}", 
                               fontsize=24, fontweight='bold', color=price_color,
                               ha='center', va='center')
    price_text.set_path_effects([
        path_effects.withStroke(linewidth=3, foreground=price_color, alpha=0.2)
    ])
    
    # Main visualization
    viz_ax = fig.add_subplot(gs[7:, 0:24])
    viz_ax.set_facecolor(bg_color)
    
    # Remove spines
    for spine in viz_ax.spines.values():
        spine.set_visible(False)
    
    # Calculate max for scaling
    max_value = max(fair_value, current_price) * 1.2  # Add 20% buffer
    
    # Prepare gradient effects
    try:
        value_lighter = lighten_color(value_color)
        price_lighter = lighten_color(price_color)
        
        value_cmap = LinearSegmentedColormap.from_list('value_grad', [
            value_color, value_lighter
        ])
        
        price_cmap = LinearSegmentedColormap.from_list('price_grad', [
            price_color, price_lighter
        ])
    except Exception as e:
        print(f"Error creating gradients: {e}")
        value_cmap = None
        price_cmap = None
    
    # Bar chart settings
    bar_height = 0.2
    spacing = 0.15
    
    # Intrinsic Value bar
    intrinsic_bar = viz_ax.barh(0.7, fair_value, height=bar_height, 
                               color=value_color, alpha=0.9,
                               edgecolor=value_color, linewidth=1)
    
    # Add gradient to intrinsic bar
    if value_cmap is not None:
        try:
            for bar in intrinsic_bar:
                x, y = bar.get_xy()
                w, h = bar.get_width(), bar.get_height()
                gradient = np.linspace(0, 1, 100).reshape(1, -1)
                viz_ax.imshow(gradient, cmap=value_cmap, aspect='auto', 
                            extent=[x, x+w, y, y+h], alpha=0.6)
        except Exception as e:
            print(f"Error applying gradient: {e}")
    
    # Add value label inside bar if there's enough space
    if fair_value > max_value * 0.15:
        viz_ax.text(fair_value/2, 0.7, "INTRINSIC", 
                  fontsize=12, fontweight='bold', color='white', 
                  ha='center', va='center')
    
    # Add value label at end of bar
    viz_ax.text(fair_value + (max_value * 0.01), 0.7, f"${fair_value:.2f}", 
              fontsize=12, fontweight='bold', color=value_color, 
              ha='left', va='center')
    
    # Current Price bar
    price_bar = viz_ax.barh(0.7 - spacing - bar_height, current_price, 
                           height=bar_height, color=price_color, alpha=0.9,
                           edgecolor=price_color, linewidth=1)
    
    # Add gradient to price bar
    if price_cmap is not None:
        try:
            for bar in price_bar:
                x, y = bar.get_xy()
                w, h = bar.get_width(), bar.get_height()
                gradient = np.linspace(0, 1, 100).reshape(1, -1)
                viz_ax.imshow(gradient, cmap=price_cmap, aspect='auto', 
                            extent=[x, x+w, y, y+h], alpha=0.6)
        except Exception as e:
            print(f"Error applying price gradient: {e}")
    
    # Add price label inside bar if there's enough space
    if current_price > max_value * 0.15:
        viz_ax.text(current_price/2, 0.7 - spacing - bar_height, "PRICE", 
                  fontsize=12, fontweight='bold', color='white', 
                  ha='center', va='center')
    
    # Add price label at end of bar
    viz_ax.text(current_price + (max_value * 0.01), 0.7 - spacing - bar_height, 
              f"${current_price:.2f}", fontsize=12, fontweight='bold', 
              color=price_color, ha='left', va='center')
    
    # Add grid lines
    for x in np.linspace(0, max_value, 6):
        viz_ax.axvline(x, color=grid_color, linestyle='-', linewidth=0.5, alpha=0.2)
    
    # Set axis limits
    viz_ax.set_xlim(0, max_value)
    viz_ax.set_ylim(0.3, 0.9)
    
    # Hide ticks but show subtle x-axis labels
    viz_ax.set_yticks([])
    viz_ax.set_xticks(np.linspace(0, max_value, 6))
    viz_ax.set_xticklabels([f"${x:.0f}" for x in np.linspace(0, max_value, 6)], 
                          color=subtext_color, fontsize=10)
    
    # Add watermark
    fig.text(0.98, 0.01, "PREMIUM VALUATION", fontsize=8, alpha=0.4,
           color=subtext_color, ha='right', va='bottom')
    
    # Add timestamp
    today = datetime.now().strftime("%d %b %Y")
    fig.text(0.02, 0.01, f"Generated: {today}", fontsize=8, 
           color=subtext_color, ha='left', va='bottom')
    
    # Final layout adjustments
    plt.tight_layout(pad=1.2)
    
    # Convert to base64
    buf = BytesIO()
    plt.savefig(buf, format='png', facecolor=bg_color, dpi=120)
    buf.seek(0)
    plt.close(fig)
    
    # Return encoded image
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def generate_simple_valuation_chart(ticker, dark_theme=True):
    """Emergency fallback function if the premium chart fails"""
    ticker = ticker.upper()
    current_price, company_name = get_current_price(ticker)
    fair_value = FAIR_VALUE_DATA.get(ticker, {}).get("fair_value", 0)
    
    # Calculate metrics
    diff = fair_value - current_price
    diff_pct = (diff / current_price * 100) if current_price > 0 else 0
    is_undervalued = diff > 0
    
    # Simple color scheme
    if dark_theme:
        bg_color = '#171B26'
        text_color = '#FFFFFF'
        value_color = '#00D09C' if is_undervalued else '#FF5757'
        price_color = '#5D87FF'
    else:
        bg_color = '#FFFFFF'
        text_color = '#1E293B'
        value_color = '#10B981' if is_undervalued else '#EF4444'
        price_color = '#3B82F6'
    
    status_text = "UNDERVALUED" if is_undervalued else "OVERVALUED"
    sign = "+" if is_undervalued else ""
    
    # Create simple figure
    plt.figure(figsize=(10, 6), facecolor=bg_color)
    
    # Title
    plt.text(0.05, 0.95, f"{ticker} Intrinsic vs Current", 
           fontsize=18, fontweight='bold', color=text_color, transform=plt.gca().transAxes)
    plt.text(0.05, 0.9, f"{sign}${diff:.2f} ({sign}{diff_pct:.1f}%)",
           fontsize=14, color=value_color, transform=plt.gca().transAxes)
    
    # Simple bar chart
    max_value = max(fair_value, current_price) * 1.1
    plt.barh(2, fair_value, color=value_color, alpha=0.8, height=0.5)
    plt.barh(1, current_price, color=price_color, alpha=0.8, height=0.5)
    
    # Labels
    plt.text(max_value * 0.02, 2, "Intrinsic", va='center', color=text_color)
    plt.text(max_value * 0.02, 1, "Price", va='center', color=text_color)
    plt.text(fair_value + max_value * 0.01, 2, f"${fair_value:.2f}", va='center', color=value_color)
    plt.text(current_price + max_value * 0.01, 1, f"${current_price:.2f}", va='center', color=price_color)
    
    # Clean up plot
    plt.axis('off')
    plt.xlim(0, max_value)
    plt.ylim(0.5, 2.5)
    
    # Save to buffer
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', facecolor=bg_color)
    buf.seek(0)
    plt.close()
    
    # Return encoded image
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def generate_enhanced_valuation_chart(ticker, dark_theme=True):
    """Wrapper function to maintain compatibility with your existing code"""
    try:
        return generate_premium_valuation_chart(ticker, dark_theme)
    except Exception as e:
        print(f"Error in premium chart generation: {e}")
        return generate_simple_valuation_chart(ticker, dark_theme)