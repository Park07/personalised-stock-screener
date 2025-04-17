import requests
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from datetime import datetime
import pandas as pd
import matplotlib.ticker as mtick
from config import FMP_API_KEY
import traceback
import json

BASE_URL = "https://financialmodelingprep.com/api/v3/"

def generate_quarterly_performance_chart(ticker, quarters=4, dark_theme=True):
    # Generate a quarterly performance chart comparing revenue and earnings.
    income_url = f"{BASE_URL}income-statement/{ticker}?period=quarter&limit={quarters}&apikey={FMP_API_KEY}"
    
    print(f"DEBUG: Fetching quarterly financials from: {income_url}")
    try:
        # DEBUG: Print API key info without revealing full key
        api_key_preview = FMP_API_KEY[:4] + "..." if FMP_API_KEY else "None"
        print(f"DEBUG: Using API key starting with: {api_key_preview}")
        
        response = requests.get(income_url)
        print(f"DEBUG: API Response status code: {response.status_code}")
        print(f"DEBUG: API Response headers: {json.dumps(dict(response.headers), indent=2)}")
        
        if response.status_code != 200:
            print(f"WARNING: Failed to fetch quarterly financials, status: {response.status_code}")
            print(f"DEBUG: Response content: {response.text[:500]}")
            return None
            
        statements = response.json()
        print(f"DEBUG: Received {len(statements)} quarterly statements")
        
        if not statements or len(statements) < 1:
            print(f"WARNING: No quarterly data available for {ticker}")
            return None
        
        # DEBUG: Print the first statement structure
        print(f"DEBUG: First statement structure: {json.dumps(statements[0], indent=2)[:500]}...")
            
        # Initialize financial data structure
        quarters_labels = []
        revenue = []
        earnings = []
        date_objects = []  # For sorting
        
        # Extract quarterly data
        for i, statement in enumerate(statements):
            # Extract date (fiscal quarter end date)
            date = statement.get("date", "")
            if not date:
                print(f"DEBUG: Statement {i} missing date field")
                continue
                
            # Parse date and create quarter label (Q1'24, Q2'24, etc.)
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
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
                
                # Extract revenue and earnings
                revenue_value = statement.get("revenue", 0)
                earnings_value = statement.get("netIncome", 0)
                
                print(f"DEBUG: Processing {date} as {quarter_label} - Revenue: ${revenue_value/1e9:.2f}B, Earnings: ${earnings_value/1e9:.2f}B")
                
                quarters_labels.append(quarter_label)
                date_objects.append(date_obj)
                revenue.append(revenue_value)
                earnings.append(earnings_value)
                
            except Exception as e:
                print(f"WARNING: Error processing date {date}: {e}")
                print(f"DEBUG: Exception details: {traceback.format_exc()}")
                continue
        
        print(f"DEBUG: Extracted data for {len(quarters_labels)} quarters")
        
        # Sort data by date (recent quarters first)
        if date_objects:
            print(f"DEBUG: Sorting data by date (descending)")
            # Create a list of tuples with all data
            combined = list(zip(date_objects, quarters_labels, revenue, earnings))
            
            # Sort by date (descending)
            combined.sort(reverse=True)
            
            # Unpack the sorted data
            date_objects = [item[0] for item in combined]
            quarters_labels = [item[1] for item in combined]
            revenue = [item[2] for item in combined]
            earnings = [item[3] for item in combined]
            
            print(f"DEBUG: Sorted quarters: {quarters_labels}")
        
        # Convert to billions for display
        revenue_billions = [r / 1e9 for r in revenue]
        earnings_billions = [e / 1e9 for e in earnings]
        
        print(f"DEBUG: Revenue (billions): {[f'${r:.2f}B' for r in revenue_billions]}")
        print(f"DEBUG: Earnings (billions): {[f'${e:.2f}B' for e in earnings_billions]}")
        
        # Set up the figure with dark theme if requested
        if dark_theme:
            print(f"DEBUG: Using dark theme for chart")
            plt.style.use('dark_background')
            bar_colors = ['#3a86ff', '#ffd166']  # Blue and gold for dark theme
            text_color = 'white'
            grid_color = '#555555'
        else:
            print(f"DEBUG: Using light theme for chart")
            plt.style.use('default')
            bar_colors = ['#4e79a7', '#f28e2b']  # Blue and orange for light theme
            text_color = 'black'
            grid_color = '#cccccc'
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Set bar width and positions
        bar_width = 0.35
        x = np.arange(len(quarters_labels))
        
        # Create bars
        revenue_bars = ax.bar(x - bar_width/2, revenue_billions, bar_width, label='Revenue', color=bar_colors[0])
        earnings_bars = ax.bar(x + bar_width/2, earnings_billions, bar_width, label='Earnings', color=bar_colors[1])
        
        # Add a title and custom styling
        name = ticker
        try:
            # Try to get the company name from profile
            print(f"DEBUG: Fetching company profile for {ticker}")
            profile_url = f"{BASE_URL}search?query={ticker}&apikey={FMP_API_KEY}"
            print(f"DEBUG: Profile URL: {profile_url}")
            
            response = requests.get(profile_url)
            print(f"DEBUG: Profile API response status: {response.status_code}")
            
            if response.status_code == 200:
                profile_data = response.json()
                print(f"DEBUG: Received {len(profile_data)} search results")
                
                if profile_data and len(profile_data) > 0:
                    company_name = profile_data[0].get("name", ticker)
                    print(f"DEBUG: Found company name: {company_name}")
                else:
                    company_name = ticker
                    print(f"DEBUG: No company profile found, using ticker as name")
            else:
                company_name = ticker
                print(f"DEBUG: Failed to fetch company profile, using ticker as name")
        except Exception as e:
            company_name = ticker
            print(f"DEBUG: Error fetching company profile: {e}")
            print(f"DEBUG: {traceback.format_exc()}")
        
        chart_title = f'{company_name}: Revenue vs. Earnings'
        print(f"DEBUG: Using chart title: {chart_title}")
        ax.set_title(chart_title, fontsize=22, pad=20, color=text_color, fontweight='bold')
        
        # Create a custom legend with current values
        latest_revenue = revenue_billions[0] if revenue_billions else 0
        latest_earnings = earnings_billions[0] if earnings_billions else 0
        
        legend_text = [
            f'Revenue {latest_revenue:.1f}B',
            f'Earnings {latest_earnings:.1f}B'
        ]
        
        print(f"DEBUG: Legend text: {legend_text}")
        
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
        ax.set_xticklabels(quarters_labels, fontsize=12)
        
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
        max_value = max(max(revenue_billions, default=0), max(earnings_billions, default=0))
        if max_value > 0:
            step = max_value / 5  # Create approximately 5 steps
            
            # Round step to a nice number
            magnitude = 10 ** np.floor(np.log10(step))
            step = np.ceil(step / magnitude) * magnitude
            
            y_ticks = np.arange(0, max_value + step, step)
            ax.set_yticks(y_ticks)
            print(f"DEBUG: Y-axis ticks: {y_ticks}")
        
        print(f"DEBUG: Applying tight layout")
        plt.tight_layout()
        
        # Save the figure to a bytes buffer
        print(f"DEBUG: Saving chart to buffer")
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to base64 string
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        print(f"DEBUG: Chart generated successfully, base64 length: {len(img_str)} chars")
        plt.close(fig)
        
        return img_str
    
    except Exception as e:
        print(f"ERROR: Failed to generate quarterly performance chart: {e}")
        print(f"DEBUG: Detailed exception information:")
        traceback.print_exc()
        return None

# Flask endpoint example (commented out)
"""
@app.route('/fundamentals/quarterly-performance', methods=['GET'])
@app.route('/fundamentals_historical/generate_quarterly_performance_chart', methods=['GET'])
def quarterly_performance_endpoint():
    ticker = request.args.get('ticker')
    if not ticker:
        print(f"DEBUG: Missing ticker parameter")
        return jsonify({'error': 'Ticker parameter is required'}), 400
            
    try:
        quarters = int(request.args.get('quarters', '4'))
        if quarters < 1 or quarters > 12:
            print(f"DEBUG: Invalid quarters value: {quarters}")
            return jsonify({'error': 'Quarters must be between 1 and 12'}), 400
    except ValueError:
        print(f"DEBUG: Non-integer quarters value")
        return jsonify({'error': 'Quarters must be a valid integer'}), 400
        
    dark_theme = request.args.get('dark_theme', 'true').lower() == 'true'
    response_format = request.args.get('format', 'json')
        
    if response_format not in ['json', 'png']:
        print(f"DEBUG: Invalid format: {response_format}")
        return jsonify({'error': 'Format must be either "json" or "png"'}), 400
    
    print(f"DEBUG: Processing request - ticker: {ticker}, quarters: {quarters}, format: {response_format}")
        
    # Generate the chart
    img_str = generate_quarterly_performance_chart(ticker, quarters, dark_theme)
        
    if not img_str:
        print(f"DEBUG: Chart generation failed")
        return jsonify({'error': 'Failed to generate chart'}), 500
        
    # Return based on requested format
    if response_format == 'json':
        print(f"DEBUG: Returning JSON response")
        return jsonify({
            'ticker': ticker,
            'chart': img_str
        })
    else:  # PNG format
        print(f"DEBUG: Returning PNG response")
        img_data = base64.b64decode(img_str)
        return Response(
            img_data,
            mimetype='image/png',
            headers={
                'Content-Disposition': f'attachment; filename={ticker}_quarterly_performance.png'
            }
        )
"""

# Example of standalone testing
if __name__ == "__main__":
    print("DEBUG: Running standalone test")
    ticker = "AAPL"
    img_str = generate_quarterly_performance_chart(ticker, quarters=4, dark_theme=True)
    
    if img_str:
        print(f"DEBUG: Chart generated successfully, saving to file")
        img_data = base64.b64decode(img_str)
        with open(f"{ticker}_quarterly_chart.png", "wb") as f:
            f.write(img_data)
        print(f"DEBUG: Chart saved to {ticker}_quarterly_chart.png")
    else:
        print("DEBUG: Failed to generate chart")