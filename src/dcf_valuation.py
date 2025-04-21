from datetime import datetime
from io import BytesIO
import base64
from matplotlib import gridspec
import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image
from fundamentals import get_fmp_valuation_data
from config import FMP_API_KEY

# Base URLs for API calls
BASE_URL = "https://financialmodelingprep.com/api/v3/"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"


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
    'AMZN': {"fair_value": 35.99025837057056, "valuation_status": "Overvalued"},
    'JPM': {"fair_value": 85.73865380104637, "valuation_status": "Overvalued"},
    'ADBE': {"fair_value": 306.1240311714045, "valuation_status": "Overvalued"},
    'CRM': {"fair_value": 289.5487901230884, "valuation_status": "Undervalued"},
    'AMD': {"fair_value": 28.78959059764345, "valuation_status": "Overvalued"},
    'PYPL': {"fair_value": 98.2473820072602, "valuation_status": "Undervalued"},
    'PG': {"fair_value": 254.69772167989305, "valuation_status": "Undervalued"},
    'KO': {"fair_value": 29.8456918830064, "valuation_status": "Overvalued"},
    'PEP': {"fair_value":152.44151778169382, "valuation_status": "Undervalued"},
    'WMT': {"fair_value":136.06271619208434, "valuation_status": "Undervalued"},
    'COST': {"fair_value": 295.06816387800217, "valuation_status": "Overvalued"},
    'PM': {"fair_value": 215.77643061457027, "valuation_status": "Undervalued"},
    'HD': {"fair_value": 236.2232262019357, "valuation_status": "Overvalued"},
    'ABBV': {"fair_value": 275.87380950821534, "valuation_status": "Undervalued"},
    'TXN': {"fair_value": 28.358290461732132, "valuation_status": "Overvalued"},
    'CVX': {"fair_value": 247.71643477084137, "valuation_status": "Undervalued"},
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
        # Direct PNG URLs for better compatibility
        logo_map = {
            'AAPL': 'https://1000logos.net/wp-content/uploads/2016/10/Apple-Logo.png',
            'MSFT': 'https://1000logos.net/wp-content/uploads/2017/04/Microsoft-Logo.png',
            'GOOG': 'https://1000logos.net/wp-content/uploads/2021/05/Google-logo.png',
            'NVDA': 'https://1000logos.net/wp-content/uploads/2017/08/NVIDIA-Symbol.png',
            'TSLA': 'https://1000logos.net/wp-content/uploads/2018/02/Tesla-logo.png',
            'SBUX': 'https://1000logos.net/wp-content/uploads/2017/03/Starbucks-Logo.png',
        }

        # Fallback to alternative
        alt_logo_map = {
            'AAPL': ('https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/'
                    'Apple_logo_black.svg/320px-Apple_logo_black.svg.png'),
            'MSFT': ('https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/'
                    'Microsoft_logo.svg/320px-Microsoft_logo.svg.png'),
            'GOOG': ('https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/'
                    'Google_2015_logo.svg/320px-Google_2015_logo.svg.png'),
            'NVDA': ('https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/'
                    'Nvidia_logo.svg/320px-Nvidia_logo.svg.png'),
            'SBUX': ('https://upload.wikimedia.org/wikipedia/en/thumb/d/d3/'
                    'Starbucks_Corporation_Logo_2011.svg/' 
                    '320px-Starbucks_Corporation_Logo_2011.svg.png'),
        }

        # Try the main source first, then fallback
        return logo_map.get(ticker) or alt_logo_map.get(ticker)
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
    url = (
        f"{BASE_URL}cash-flow-statement/{ticker}?"
           f"period={period}&limit={limit}&apikey={FMP_API_KEY}"
        )
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
        wacc = (equity_weight * cost_of_equity) + \
            (debt_weight * after_tax_cost_of_debt)
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
        stmt.get(
            "freeCashFlow",
            0) for stmt in cash_flow_statements if stmt.get(
            "freeCashFlow",
            0) != 0]
    if not historical_fcf:
        print(f"No historical FCF data available for {ticker}")
        return None
    fcf_growth_rates = [(historical_fcf[i - 1] / historical_fcf[i]
                         ) - 1 for i in range(1, len(historical_fcf))]
    if fcf_growth_rates:
        historical_growth_rate = np.median(fcf_growth_rates)
    else:
        historical_growth_rate = (
            growth_data[0].get(
                "freeCashFlowGrowth",
                0.05) if growth_data else 0.05)
    historical_growth_rate = max(-0.20, min(historical_growth_rate, 0.25))
    latest_fcf = historical_fcf[0]
    projected_fcf = [latest_fcf *
                     (1 + historical_growth_rate) ** i for i in range(1, 6)]
    terminal_growth_rate = 0.027
    for i in range(6, years + 1):
        stage = i - 5
        transition_weight = stage / 5
        current_growth = historical_growth_rate * \
            (1 - transition_weight) + terminal_growth_rate * transition_weight
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
    pv_fcf = [fcf / ((1 + discount_rate) ** (i + 1))
              for i, fcf in enumerate(projected_fcf)]
    terminal_fcf = projected_fcf[-1] * (1 + terminal_growth_rate)
    terminal_value = (terminal_fcf /
                 (discount_rate - terminal_growth_rate))
    pv_terminal_value = terminal_value / \
        ((1 + discount_rate) ** len(projected_fcf))
    enterprise_value = sum(pv_fcf) + pv_terminal_value
    net_debt = 0
    try:
        balance_sheet_url = (
                            f"{BASE_URL}balance-sheet-statement/"
                            f"{ticker}?limit=1&apikey={FMP_API_KEY}"
                            )
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


def generate_minimalist_valuation_chart(ticker, dark_theme=True):
    """Generate a minimalist valuation chart highlighting the gap between values"""
    ticker = ticker.upper()

    # Get data using your original functions
    current_price, company_name = get_current_price(ticker)
    fair_value = FAIR_VALUE_DATA.get(ticker, {}).get("fair_value", 0)

    # Calculate metrics
    diff = fair_value - current_price
    diff_pct = (diff / current_price * 100) if current_price > 0 else 0
    is_undervalued = diff > 0

    # Modern minimalist colour schemes (Australian English spelling)
    if dark_theme:
        bg_color = '#131722'
        text_color = '#FFFFFF'
        subtext_color = '#8F96A3'
        value_color = '#F0B90B'  # Gold
        price_color = '#30B5FF'  # Blue
        undervalued_color = '#26A69A'  # Teal
        overvalued_color = '#EF5350'  # Red
        axis_color = '#2A2E39'
        gap_color = '#EF5350' if not is_undervalued else '#26A69A'
    else:
        bg_color = '#FFFFFF'
        text_color = '#1E293B'
        subtext_color = '#64748B'
        value_color = '#F59E0B'  # Amber
        price_color = '#3B82F6'  # Blue
        undervalued_color = '#10B981'  # Green
        overvalued_color = '#EF4444'  # Red
        axis_color = '#E2E8F0'
        gap_color = '#EF4444' if not is_undervalued else '#10B981'

    # Set up figure with clean design
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 12,
        'axes.facecolor': bg_color,
        'figure.facecolor': bg_color,
        'text.color': text_color,
        'axes.labelcolor': text_color,
        'xtick.color': subtext_color,
        'ytick.color': subtext_color
    })

    # Create figure with wider aspect ratio to match your example
    fig = plt.figure(figsize=(12, 6), dpi=120)

    # Create grid layout
    gs = gridspec.GridSpec(8, 12, figure=fig)

    # Header section
    header_ax = fig.add_subplot(gs[0:2, 0:9])
    header_ax.axis('off')

    # Title with ticker
    header_ax.text(
        0,
        0.7,
        ticker,
        fontsize=28,
        fontweight='bold',
        color=text_color)

    # Company name
    header_ax.text(0, 0.3, company_name, fontsize=16, color=subtext_color)

    # Logo section
    logo_ax = fig.add_subplot(gs[0:2, 9:])
    logo_ax.axis('off')

    # Display logo if available - with better handling for different image
    # types
    logo_url = get_company_logo(ticker)

    if logo_url:
        try:
            response = requests.get(logo_url, timeout=5)

            if response.status_code == 200:
                # Better handling for various image formats
                img_data = BytesIO(response.content)

                try:
                    img = Image.open(img_data)

                    # Resize to reasonable dimensions
                    max_size = (200, 200)
                    img.thumbnail(max_size, Image.LANCZOS)

                    # Handle transparency for dark/light themes
                    if img.mode == 'RGBA':
                        # Create background matching the theme
                        bg = Image.new(
                            'RGBA', img.size, (19, 23, 34, 255) if dark_theme else (
                                255, 255, 255, 255))
                        # Paste using the alpha channel as mask
                        bg.paste(img, (0, 0), img)
                        img = bg.convert('RGB')
                    img = img.rotate(180)
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)

                    # Display the image
                    logo_ax.imshow(img)
                    logo_ax.set_xlim(0, img.width)
                    logo_ax.set_ylim(0, img.height)

                    # Ensure all axes elements are hidden
                    logo_ax.set_xticks([])
                    logo_ax.set_yticks([])
                    for spine in logo_ax.spines.values():
                        spine.set_visible(False)
                except Exception as e:
                    # Fallback - display the first letter as a logo
                    logo_ax.text(
                        0.5,
                        0.5,
                        ticker[0],
                        fontsize=40,
                        fontweight='bold',
                        ha='center',
                        va='center',
                        color=text_color)
            else:
                # Fallback - display the first letter as a logo
                logo_ax.text(
                    0.5,
                    0.5,
                    ticker[0],
                    fontsize=40,
                    fontweight='bold',
                    ha='center',
                    va='center',
                    color=text_color)
        except Exception as e:
            # Fallback - just display the first letter as a logo
            logo_ax.text(0.5, 0.5, ticker[0], fontsize=40, fontweight='bold',
                         ha='center', va='center', color=text_color)
    else:
        # Fallback when no logo URL is found
        logo_ax.text(0.5, 0.5, ticker[0], fontsize=40, fontweight='bold',
                     ha='center', va='center', color=text_color)

    # Current price section (large)
    price_ax = fig.add_subplot(gs[2:4, :])
    price_ax.axis('off')

    # Current price with large font (using Australian English format)
    price_ax.text(0, 0.6, "CURRENT PRICE", fontsize=14, color=subtext_color)
    price_ax.text(0,
                  0.2,
                  f"${current_price:.2f}",
                  fontsize=36,
                  fontweight='bold',
                  color=price_color)

    # Valuation status - remove from here as we'll add it directly in the gap
    status_text = "OVERVALUED" if diff_pct < 0 else "UNDERVALUED"
    status_color = overvalued_color if diff_pct < 0 else undervalued_color

    # Visualisation section
    vis_ax = fig.add_subplot(gs[4:, :])
    vis_ax.set_facecolor(bg_color)

    # Remove all spines
    for spine in vis_ax.spines.values():
        spine.set_visible(False)

    # Determine scale for visualization
    max_value = max(current_price, fair_value) * 1.1

    # Create bars with clean, minimalist style
    bar_height = 0.3
    y_intrinsic = 0.65
    y_price = 0.3

    # Position labels more to the left with negative offset
    label_offset = -max_value * 0.05  # Negative offset moves labels to the left

    # Draw intrinsic value bar
    intrinsic_bar = vis_ax.barh(
        y_intrinsic,
        fair_value,
        height=bar_height,
        color=value_color,
        alpha=0.9)
    vis_ax.text(
        label_offset,
        y_intrinsic,
        "INTRINSIC",
        ha='right',
        va='center',
        color=subtext_color,
        fontsize=12)

    # Draw price bar
    price_bar = vis_ax.barh(
        y_price,
        current_price,
        height=bar_height,
        color=price_color,
        alpha=0.9)
    vis_ax.text(label_offset, y_price, "PRICE", ha='right', va='center',
                color=subtext_color, fontsize=12)
    vis_ax.text(current_price + max_value * 0.01,
                y_price,
                f"${current_price:.2f}",
                va='center',
                color=price_color,
                fontsize=14,
                fontweight='bold')

    # Highlight the gap between values
    if is_undervalued:
        # Intrinsic > Price
        gap_start = current_price
        gap_width = fair_value - current_price
        gap_y = y_price
        diff_value = fair_value - current_price
    else:
        # Price > Intrinsic
        gap_start = fair_value
        gap_width = current_price - fair_value
        gap_y = y_intrinsic
        diff_value = current_price - fair_value

    # Draw gap highlight with more pronounced hatching
    vis_ax.barh(gap_y, gap_width, left=gap_start, height=bar_height,
                color=gap_color, alpha=0.3, hatch='//////')

    # Draw vertical lines and gap label for overvalued/undervalued
    if not is_undervalued:  # If overvalued
        # First vertical line at intrinsic value
        vis_ax.axvline(x=fair_value, ymin=0, ymax=1, color=overvalued_color,
                       linestyle='-', linewidth=2, alpha=0.8)

        # Second vertical line at current price
        vis_ax.axvline(x=current_price, ymin=0, ymax=1, color=overvalued_color,
                       linestyle='-', linewidth=2, alpha=0.8)

        # Remove the left-side texts since they're redundant
        # Only show the fair value at the right side of the second red line
        vis_ax.text(current_price + max_value * 0.01, y_intrinsic,
                    f"${fair_value:.2f}",
                    color=value_color, fontsize=14, fontweight='bold',
                    ha='left', va='center')

        # Show the difference in red right after the fair value
        vis_ax.text(fair_value + (max_value * 0.02) + len(f"${fair_value:.2f}"),
                    y_intrinsic,
                    f"${diff_value:.2f}",
                    color=overvalued_color,
                    fontsize=14,
                    fontweight='bold',
                    ha='left',
                    va='center')

        # Add percentage overvalued along the top of the gap
        vis_ax.text((fair_value + current_price) / 2, 0.9,
                    f"{abs(diff_pct):.1f}% OVERVALUED",
                    color=overvalued_color, fontsize=15, fontweight='bold',
                    ha='center', va='center')
    else:
        # Similar treatment but for undervalued (green lines)
        vis_ax.axvline(
            x=current_price,
            ymin=0,
            ymax=1,
            color=undervalued_color,
            linestyle='-',
            linewidth=2,
            alpha=0.8)

        vis_ax.axvline(x=fair_value, ymin=0, ymax=1, color=undervalued_color,
                       linestyle='-', linewidth=2, alpha=0.8)

        # Add the gap value in the middle of the gap, aligned with the price
        # bar
        vis_ax.text((current_price + fair_value) / 2, y_price,
                    f"+${diff_value:.2f}",
                    color=undervalued_color, fontsize=14, fontweight='bold',
                    ha='center', va='center')

        # Add percentage undervalued along the top of the gap
        vis_ax.text((current_price + fair_value) / 2, 0.9,
                    f"{abs(diff_pct):.1f}% UNDERVALUED",
                    color=undervalued_color, fontsize=16, fontweight='bold',
                    ha='center', va='center')

    # Add subtle grid
    for x in np.linspace(0, max_value, 6):
        vis_ax.axvline(
            x,
            color=axis_color,
            linestyle='-',
            linewidth=0.5,
            alpha=0.2)

    # Set axis limits with some padding
    # More padding on the left for the labels
    vis_ax.set_xlim(-max_value * 0.15, max_value * 1.05)
    vis_ax.set_ylim(0, 1)

    # X-axis labels (minimalist)
    vis_ax.set_xticks(np.linspace(0, max_value, 6))
    vis_ax.set_xticklabels([f"${x:.0f}" for x in np.linspace(0, max_value, 6)],
                           fontsize=10, color=subtext_color)
    vis_ax.tick_params(axis='x', which='both', length=0)  # Hide tick marks
    vis_ax.set_yticks([])

    # Tight layout
    plt.tight_layout(pad=1.0)

    # Convert to base64
    buf = BytesIO()
    plt.savefig(buf, format='png', facecolor=bg_color, dpi=120)
    buf.seek(0)
    plt.close(fig)

    return base64.b64encode(buf.getvalue()).decode('utf-8')


def generate_enhanced_valuation_chart(ticker, dark_theme=True):
    """Wrapper function to maintain compatibility with existing code"""
    try:
        return generate_minimalist_valuation_chart(ticker, dark_theme)
    except Exception as e:
        print(f"Error generating chart: {e}")
        # Fall back to a very simple chart if needed
        return generate_simple_fallback_chart(ticker, dark_theme)


def generate_simple_fallback_chart(ticker, dark_theme=True):
    """Ultra-simple fallback in case of errors"""
    ticker = ticker.upper()
    current_price, company_name = get_current_price(ticker)
    fair_value = FAIR_VALUE_DATA.get(ticker, {}).get("fair_value", 0)

    # Simple colors
    bg_color = '#131722' if dark_theme else '#FFFFFF'
    text_color = '#FFFFFF' if dark_theme else '#1E293B'

    # Create very simple figure
    plt.figure(figsize=(8, 4), facecolor=bg_color)
    ax = plt.gca()
    ax.text(0.5, 0.8, f"{ticker}: ${current_price:.2f}",
            fontsize=16, fontweight='bold', color=text_color,
            ha='center', transform=ax.transAxes)
    ax.text(0.5, 0.6, f"Intrinsic Value: ${fair_value:.2f}",
            fontsize=14, color=text_color,
            ha='center', transform=ax.transAxes)
    ax.text(0.5, 0.4, company_name,
            fontsize=12, color=text_color,
            ha='center', transform=ax.transAxes)

    # Hide everything
    ax.axis('off')

    # Save
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', facecolor=bg_color)
    buf.seek(0)
    plt.close()

    return base64.b64encode(buf.getvalue()).decode('utf-8')
