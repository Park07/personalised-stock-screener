from flask import Flask, request, jsonify, Response
import requests
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from datetime import datetime
import pandas as pd
import matplotlib.ticker as mtick
import traceback
import json
import os
from matplotlib.patches import Patch
import time

app = Flask(__name__)

from config import ALPHA_VANTAGE_API_KEY



ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def get_alpha_vantage_yearly_data(ticker, years=4, retries=3):
    """Get yearly revenue and earnings from Alpha Vantage with retries"""
    print(f"INFO: Fetching live Alpha Vantage yearly data for {ticker}")
    
    today = datetime.utcnow().date()
    for attempt in range(retries):
        try:
            # Get company overview for basic info
            overview_params = {
                "function": "OVERVIEW",
                "symbol": ticker,
                "apikey": ALPHA_VANTAGE_API_KEY
            }
            
            print(f"DEBUG: Fetching company overview from Alpha Vantage (attempt {attempt+1}/{retries})")
            overview_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=overview_params, timeout=10)
            print(f"DEBUG: Overview response status: {overview_response.status_code}")
            
            company_name = ticker
            if overview_response.status_code == 200:
                overview_data = overview_response.json()
                if "Name" in overview_data:
                    company_name = overview_data["Name"]
                    print(f"INFO: Company name: {company_name}")
                elif not overview_data:
                    print(f"WARNING: Empty response for company overview")
                else:
                    print(f"WARNING: No name found in overview data: {overview_data.keys()}")
            else:
                print(f"WARNING: Failed to get company overview, status: {overview_response.status_code}")
                if attempt < retries - 1:
                    # Wait before retrying to avoid rate limits
                    print(f"INFO: Waiting 2 seconds before retrying...")
                    time.sleep(2)
                    continue
            
            # Get annual income statement
            income_params = {
                "function": "INCOME_STATEMENT",
                "symbol": ticker,
                "apikey": ALPHA_VANTAGE_API_KEY
            }
            
            print(f"DEBUG: Fetching income statement from Alpha Vantage (attempt {attempt+1}/{retries})")
            income_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=income_params, timeout=10)
            print(f"DEBUG: Income statement response status: {income_response.status_code}")
            
            if income_response.status_code != 200:
                print(f"WARNING: Failed to fetch income data, status: {income_response.status_code}")
                print(f"DEBUG: Response content: {income_response.text[:500]}")
                if attempt < retries - 1:
                    # Wait before retrying to avoid rate limits
                    print(f"INFO: Waiting 2 seconds before retrying...")
                    time.sleep(2)
                    continue
                return None, company_name
                
            income_data = income_response.json()
            if "Information" in income_data:
                print(f"API INFO: {income_data['Information']}")
                if "API call frequency" in income_data.get("Information", ""):
                    print("WARNING: API rate limit reached. Waiting longer before retry...")
                    time.sleep(10)  # Wait longer for rate limit issues
                    continue
            
            # Check if we have annual reports
            if "annualReports" not in income_data or not income_data["annualReports"]:
                print(f"WARNING: No annual data available in Alpha Vantage response")
                print(f"DEBUG: Available keys: {income_data.keys()}")
                if "Note" in income_data:
                    print(f"API NOTE: {income_data['Note']}")
                    
                if attempt < retries - 1:
                    # Wait longer before retrying to avoid rate limits
                    print(f"INFO: Waiting 5 seconds before retrying due to possible rate limiting...")
                    time.sleep(5)
                    continue
                return None, company_name
                
            annual_reports = income_data["annualReports"]
            print(f"INFO: Successfully retrieved {len(annual_reports)} annual reports")
            
            # Limit to requested number of years
            annual_reports = annual_reports[:years]
            
            # Process the data
            processed_data = []
            for report in annual_reports:
                fiscal_date_str = report.get("fiscalDateEnding", "")
                fiscal_date = datetime.strptime(fiscal_date_str, "%Y-%m-%d").date()
                if fiscal_date.year == today.year and (today - fiscal_date).days < 90:
                    continue

                fiscal_year = fiscal_date.year
                    
                try:
                    # Parse date to get year
                    year_label = f"FY{fiscal_year}"
                    
                    # Get financial values
                    try:
                        revenue = float(report.get("totalRevenue", 0))
                        net_income = float(report.get("netIncome", 0))
                    except (ValueError, TypeError):
                        print(f"WARNING: Invalid financial values in report for {fiscal_date}")
                        revenue = 0
                        net_income = 0
                    
                    print(f"INFO: {fiscal_date} -> {year_label}, Revenue: ${revenue/1e9:.2f}B, Income: ${net_income/1e9:.2f}B")
                    
                    processed_data.append({
                        "year": fiscal_year,
                        "label": year_label,
                        "revenue": revenue,
                        "netIncome": net_income
                    })
                    
                except Exception as e:
                    print(f"WARNING: Error processing report for {fiscal_date}: {e}")
                    continue
            
            if processed_data:
                return processed_data, company_name
            else:
                print("WARNING: No processable data found in response")
                if attempt < retries - 1:
                    continue
                return None, company_name
                
        except Exception as e:
            print(f"ERROR: Failed to fetch Alpha Vantage data (attempt {attempt+1}/{retries}): {e}")
            print(traceback.format_exc())
            if attempt < retries - 1:
                # Wait before retrying
                print(f"INFO: Waiting 3 seconds before retrying...")
                time.sleep(3)
            else:
                return None, ticker
    
    print("ERROR: All retry attempts failed")
    return None, ticker


def generate_yearly_performance_chart(ticker, years=4, dark_theme=True):
    """Generate a yearly performance chart comparing revenue and earnings."""
    print(f"INFO: Generating yearly chart for {ticker}, years={years}, dark_theme={dark_theme}")
    
    try:
        # First try to get real data from Alpha Vantage
        financial_data, company_name = get_alpha_vantage_yearly_data(ticker, years)

        if financial_data is None or len(financial_data) == 0:
            print(f"not available{financial_data}")
            return None
        
        # Sort data by year (most recent first)
        financial_data.sort(key=lambda x: x["year"])
            
        # Extract labels and financial metrics
        year_labels = [item["label"] for item in financial_data]
        revenue = [item["revenue"] for item in financial_data]
        earnings = [item["netIncome"] for item in financial_data]

        max_raw = max(max(revenue,  default=0), max(earnings, default=0))

        if max_raw >= 1e12: 
            divisor, unit = 1e12, 'T'          # Trillions
        elif max_raw >= 1e9:  
            divisor, unit = 1e9,  'B'          # Billions
        elif max_raw >= 1e6:  
            divisor, unit = 1e6,  'M'          # Millions
        elif max_raw >= 1e3:  
            divisor, unit = 1e3,  'K'          # Thousands
        else:                
            divisor, unit = 1,    ''            # Ones

        revenue_scaled  = [r / divisor for r in revenue]
        earnings_scaled = [e / divisor for e in earnings]
        
        
        print(f"INFO: Processed {len(year_labels)} years of data: {year_labels}")
        
        # Set up the figure with theme
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
        
        # Bar positions and width
        bar_width = 0.35
        x = np.arange(len(year_labels))
        
        # Create bars
        revenue_bars = ax.bar(x - bar_width/2, revenue_scaled, bar_width, label='Revenue', color=bar_colors[0])
        earnings_bars = ax.bar(x + bar_width/2, earnings_scaled, bar_width, label='Earnings', color=bar_colors[1])
        
        # Set title with company name
        chart_title = f'{company_name}: Annual Revenue vs. Earnings (YOY)'
        ax.set_title(chart_title, fontsize=22, pad=20, color=text_color, fontweight='bold')
        
        # Create custom legend with latest values
        latest_revenue = revenue_scaled[-1] 
        latest_earnings = earnings_scaled[-1] 
        
        legend_text = [
            f'Revenue {latest_revenue:.1f}{unit}',
            f'Earnings {latest_earnings:.1f}{unit}'
        ]
        
        legend_elements = [
            Patch(facecolor=bar_colors[0], label=legend_text[0]),
            Patch(facecolor=bar_colors[1], label=legend_text[1])
        ]
        
        ax.legend(handles=legend_elements, loc='upper left', frameon=False, 
                  fontsize=14, handlelength=1, handleheight=1.5)
        
        # Set x-axis ticks and labels
        ax.set_xticks(x)
        ax.set_xticklabels(year_labels, fontsize=12)
        
        # Format y-axis with billions formatter
        def billions_formatter(x, pos):
            if x == 0:
                return '0'
            return f'{x:.0f}B'
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(billions_formatter))
        
        # Add gridlines
        ax.grid(axis='y', linestyle='--', alpha=0.3, color=grid_color)
        
        # Remove unnecessary spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        if dark_theme:
            ax.spines['bottom'].set_color('#555555')
            ax.spines['left'].set_color('#555555')
        
        # Configure y-axis ticks with nice steps
        max_value = max(max(revenue_scaled, default=0), max(earnings_scaled, default=0))
        if max_value > 0:
            step = max_value / 5
            magnitude = 10 ** np.floor(np.log10(step))
            step = np.ceil(step / magnitude) * magnitude
            y_ticks = np.arange(0, max_value + step, step)
            ax.set_yticks(y_ticks)
        

        
        # Add data source info
        data_source = 'Data Source: Alpha Vantage'
        if data_source:
            ax.text(0.99, 0.01, data_source, ha='right', va='bottom',
                   transform=fig.transFigure, fontsize=8, alpha=0.7, color=text_color)
        
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to base64
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        print(f"INFO: Chart generated successfully")
        return img_str
    
    except Exception as e:
        print(f"ERROR: Failed to generate chart: {e}")
        print(traceback.format_exc())
        return None


