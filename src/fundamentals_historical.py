import requests
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.ticker as mtick
import matplotlib.dates as mdates

def get_quarterly_financials(ticker, quarters=4):
    """
    Get quarterly financial data for a company.
    
    Args:
        ticker: Company ticker symbol
        quarters: Number of quarters to retrieve (default: 4)
        
    Returns:
        Dictionary with quarterly revenue and earnings data
    """
    # Get income statements for quarterly data
    income_url = f"{BASE_URL}income-statement/quarter/{ticker}?limit={quarters}&apikey={FMP_API_KEY}"
    
    print(f"DEBUG: Fetching quarterly financials from: {income_url}")
    try:
        response = requests.get(income_url)
        if response.status_code != 200:
            print(f"WARNING: Failed to fetch quarterly financials, status: {response.status_code}")
            return None
            
        statements = response.json()
        if not statements or len(statements) < 1:
            print(f"WARNING: No quarterly data available for {ticker}")
            return None
            
        # Initialize financial data structure
        financial_data = {
            "quarters": [],
            "revenue": [],
            "earnings": [],
            "date_objects": []  # For proper chronological sorting
        }
        
        # Extract quarterly data
        for statement in statements:
            # Extract date (fiscal quarter end date)
            date = statement.get("date", "")
            if not date:
                continue
                
            # Parse date and create quarter label (Q1'24, Q2'24, etc.)
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                # Create quarter label based on month
                month = date_obj.month
                if month <= 3:
                    quarter = "Q1"
                elif month <= 6:
                    quarter = "Q2"
                elif month <= 9:
                    quarter = "Q3"
                else:
                    quarter = "Q4"
                    
                year_short = str(date_obj.year)[2:]  # Get last 2 digits of year
                quarter_label = f"{quarter}'{year_short}"
                
                financial_data["quarters"].append(quarter_label)
                financial_data["date_objects"].append(date_obj)
                
                # Extract revenue and earnings
                revenue = statement.get("revenue", 0)
                earnings = statement.get("netIncome", 0)
                
                financial_data["revenue"].append(revenue)
                financial_data["earnings"].append(earnings)
                
            except Exception as e:
                print(f"WARNING: Error processing date {date}: {e}")
                continue
        
        # Sort data by date (recent quarters first)
        if financial_data["date_objects"]:
            # Create a list of tuples with all data
            combined = list(zip(
                financial_data["date_objects"],
                financial_data["quarters"],
                financial_data["revenue"],
                financial_data["earnings"]
            ))
            
            # Sort by date (descending)
            combined.sort(reverse=True)
            
            # Unpack the sorted data
            financial_data["date_objects"] = [item[0] for item in combined]
            financial_data["quarters"] = [item[1] for item in combined]
            financial_data["revenue"] = [item[2] for item in combined]
            financial_data["earnings"] = [item[3] for item in combined]
        
        return financial_data
        
    except Exception as e:
        print(f"ERROR: Failed to get quarterly financials: {e}")
        return None

def generate_quarterly_performance_chart(ticker, quarters=4, dark_theme=True):
    """
    Generate a quarterly performance chart comparing revenue and earnings.
    
    Args:
        ticker: Company ticker symbol
        quarters: Number of quarters to retrieve
        dark_theme: Whether to use a dark theme (default: True)
        
    Returns:
        Base64 encoded PNG image
    """
    # Get quarterly financial data
    financial_data = get_quarterly_financials(ticker, quarters)
    
    if not financial_data or not financial_data["quarters"]:
        print(f"ERROR: Insufficient data to generate chart for {ticker}")
        return None
    
    # Extract the data
    quarters = financial_data["quarters"]
    revenue = financial_data["revenue"]
    earnings = financial_data["earnings"]
    
    # Convert to billions for display
    revenue_billions = [r / 1e9 for r in revenue]
    earnings_billions = [e / 1e9 for e in earnings]
    
    # Set up the figure with dark theme if requested
    if dark_theme:
        plt.style.use('dark_background')
        bar_colors = ['#3a86ff', '#ffd166']  # Blue and gold for dark theme
        text_color = 'white'
        grid_color = '#555555'
    else:
        plt.style.use('default')
        bar_colors = ['#4e79a7', '#f28e2b']  # Blue and orange for light theme
        text_color = 'black'
        grid_color = '#cccccc'
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Set bar width and positions
    bar_width = 0.35
    x = np.arange(len(quarters))
    
    # Create bars
    revenue_bars = ax.bar(x - bar_width/2, revenue_billions, bar_width, label='Revenue', color=bar_colors[0])
    earnings_bars = ax.bar(x + bar_width/2, earnings_billions, bar_width, label='Earnings', color=bar_colors[1])
    
    # Add a title and custom styling
    company_name = ticker
    try:
        # Try to get the company name from profile
        profile_url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
        response = requests.get(profile_url)
        if response.status_code == 200:
            profile_data = response.json()
            if profile_data and len(profile_data) > 0:
                company_name = profile_data[0].get("companyName", ticker)
    except:
        pass
    
    # Customize chart
    ax.set_title('Revenue vs. Earnings', fontsize=22, pad=20, color=text_color, fontweight='bold')
    
    # Create a custom legend with current values
    latest_revenue = revenue_billions[0]
    latest_earnings = earnings_billions[0]
    
    legend_text = [
        f'Revenue {latest_revenue:.1f}B',
        f'Earnings {latest_earnings:.1f}B'
    ]
    
    # Custom legend with squares instead of default markers
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=bar_colors[0], label=legend_text[0]),
        Patch(facecolor=bar_colors[1], label=legend_text[1])
    ]
    
    ax.legend(handles=legend_elements, loc='upper left', frameon=False, 
              fontsize=14, handlelength=1, handleheight=1.5)
    
    # Set x-axis ticks and labels
    ax.set_xticks(x)
    ax.set_xticklabels(quarters, fontsize=12)
    
    # Format y-axis with B suffix for billions
    def billions_formatter(x, pos):
        if x == 0:
            return '0'
        return f'{x:.0f}B'
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(billions_formatter))
    
    # Add gridlines
    ax.grid(axis='y', linestyle='--', alpha=0.3, color=grid_color)
    
    # Remove top, right and left spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    if dark_theme:
        # For dark theme, customize spine colors
        ax.spines['bottom'].set_color('#555555')
        ax.spines['left'].set_color('#555555')
    
    # Add y-axis labels with suffixes at specific positions
    max_value = max(max(revenue_billions), max(earnings_billions))
    step = max_value / 5  # Create approximately 5 steps
    
    # Round step to a nice number
    magnitude = 10 ** np.floor(np.log10(step))
    step = np.ceil(step / magnitude) * magnitude
    
    y_ticks = np.arange(0, max_value + step, step)
    ax.set_yticks(y_ticks)
    
    # Tight layout
    plt.tight_layout()
    
    # Save the figure to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    
    # Convert to base64 string
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return img_str