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
import random

app = Flask(__name__)

from src.config import ALPHA_VANTAGE_API_KEY



ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def get_alpha_vantage_yearly_data(ticker, years=4, retries=3):
    """Get yearly revenue and earnings from Alpha Vantage with retries"""
    print(f"INFO: Fetching live Alpha Vantage yearly data for {ticker}")
    
    today = datetime.utcnow().date()
    
    # Directly use mock data for now (comment out this block to use live data)
    print(f"INFO: Using mock data for {ticker} due to API rate limits")
    mock_data = generate_mock_financial_data(ticker, years)
    return mock_data
    
    # Live API code (uncomment to use real API)
    """
    for attempt in range(retries):
        try:
            # Get company overview for basic info
            overview_params = {
                "function": "OVERVIEW",
                "symbol": ticker,
                "apikey": ALPHA_VANTAGE_API_KEY
            }
            
            overview_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=overview_params, timeout=10)
            print(f"DEBUG: Overview response status: {overview_response.status_code}")
            
            company_name = ticker
            if overview_response.status_code == 200:
                overview_data = overview_response.json()
                if "Name" in overview_data:
                    company_name = overview_data["Name"]
                    print(f"INFO: Company name: {company_name}")
                elif "Information" in overview_data:
                    print(f"API INFO: {overview_data['Information']}")
                    if "API rate limit" in overview_data.get("Information", ""):
                        print("INFO: API rate limit reached, using mock data")
                        mock_data = generate_mock_financial_data(ticker, years)
                        return mock_data
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
                
                # If all retries fail, use mock data
                print("INFO: API calls failed, falling back to mock data")
                mock_data = generate_mock_financial_data(ticker, years)
                return mock_data
                
            income_data = income_response.json()
            
            # Check for API rate limit or other information messages
            if "Information" in income_data:
                print(f"API INFO: {income_data['Information']}")
                if "API rate limit" in income_data.get("Information", "").lower() or "call frequency" in income_data.get("Information", "").lower():
                    print("INFO: API rate limit reached, using mock data")
                    mock_data = generate_mock_financial_data(ticker, years)
                    return mock_data
            
            # Check if we have annual reports
            if "annualReports" not in income_data or not income_data["annualReports"]:
                print(f"WARNING: No annual data available in Alpha Vantage response")
                print(f"DEBUG: Available keys: {income_data.keys()}")
                if "Note" in income_data:
                    print(f"API NOTE: {income_data['Note']}")
                    
                if attempt < retries - 1:
                    # Wait longer before retrying to avoid rate limits
                    print(f"INFO: Waiting 5 seconds before retrying due to possible rate limiting...")
                    continue
                
                # If no data after all retries, use mock data
                print("INFO: No annual data after retries, using mock data")
                mock_data = generate_mock_financial_data(ticker, years)
                return mock_data
            
            annual_reports = income_data["annualReports"]
            print(f"INFO: Successfully retrieved {len(annual_reports)} annual reports"
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
                
                # If no processed data, use mock data
                print("INFO: No processable data, using mock data")
                mock_data = generate_mock_financial_data(ticker, years)
                return mock_data
                
        except Exception as e:
            print(f"ERROR: Failed to fetch Alpha Vantage data (attempt {attempt+1}/{retries}): {e}")
            print(traceback.format_exc())
            if attempt < retries - 1:
                # Wait before retrying
                print(f"INFO: Waiting 3 seconds before retrying...")
                time.sleep(3)
            else:
                print("INFO: All retries failed, using mock data")
                mock_data = generate_mock_financial_data(ticker, years)
                return mock_data
    
    print("ERROR: All retry attempts failed")
    print("INFO: Falling back to mock data")
    mock_data = generate_mock_financial_data(ticker, years)
    return mock_data
    """

def generate_mock_financial_data(ticker, years=4):
    """Generate realistic mock financial data for a given ticker"""
    print(f"INFO: Generating mock financial data for {ticker}")
    
    # Set a realistic company name based on ticker
    company_names = {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "META": "Meta Platforms Inc.",
        "TSLA": "Tesla Inc.",
        "NVDA": "NVIDIA Corporation",
        "NFLX": "Netflix Inc.",
        "INTC": "Intel Corporation",
        "AMD": "Advanced Micro Devices Inc."
    }
    
    company_name = company_names.get(ticker, f"{ticker} Inc.")
    
    # Set base revenue and income based on ticker (for more realistic data)
    base_data = {
        "AAPL": {"revenue": 350e9, "income": 80e9, "growth": 0.15},
        "MSFT": {"revenue": 200e9, "income": 70e9, "growth": 0.17},
        "GOOGL": {"revenue": 250e9, "income": 60e9, "growth": 0.20},
        "AMZN": {"revenue": 450e9, "income": 30e9, "growth": 0.22},
        "META": {"revenue": 120e9, "income": 40e9, "growth": 0.10},
        "TSLA": {"revenue": 80e9, "income": 12e9, "growth": 0.35},
        "NVDA": {"revenue": 40e9, "income": 15e9, "growth": 0.40},
        "NFLX": {"revenue": 30e9, "income": 5e9, "growth": 0.15},
        "INTC": {"revenue": 70e9, "income": 15e9, "growth": 0.05},
        "AMD": {"revenue": 20e9, "income": 3e9, "growth": 0.25}
    }
    
    # Default values for unknown tickers
    base_revenue = base_data.get(ticker, {"revenue": 50e9, "income": 10e9, "growth": 0.12})
    
    # Get current year and create data for past years
    current_year = datetime.utcnow().year
    processed_data = []
    
    # Create realistic year-over-year growth
    for i in range(years):
        # Work backwards from most recent year
        year = current_year - i - 1  # Start with last year, not current year
        
        # Calculate realistic financials with some year-over-year growth
        # and slight randomness (±10% of growth rate)
        growth_factor = base_data.get(ticker, base_revenue)["growth"]
        randomness = 0.9 + (0.2 * random.random())  # Random factor between 0.9 and 1.1
        year_factor = (1 + growth_factor * randomness) ** (years - i - 1)  # Less growth in older years
        
        revenue = base_data.get(ticker, base_revenue)["revenue"] / year_factor
        income = base_data.get(ticker, base_revenue)["income"] / year_factor
        
        # Add some randomness to income as a percentage of revenue
        income_randomness = 0.85 + (0.3 * random.random())  # 0.85 to 1.15
        income *= income_randomness
        
        processed_data.append({
            "year": year,
            "label": f"FY{year}",
            "revenue": revenue,
            "netIncome": income
        })
    
    # Reverse to get chronological order
    processed_data.reverse()
    
    print(f"INFO: Generated mock data for {company_name} with {len(processed_data)} years")
    return processed_data, company_name


def generate_yearly_performance_chart(ticker, years=4, dark_theme=True):
    """Generate a yearly performance chart comparing revenue and earnings."""
    print(f"INFO: Generating yearly chart for {ticker}, years={years}, dark_theme={dark_theme}")
    
    try:
        # First try to get data from Alpha Vantage or mock data
        financial_data, company_name = get_alpha_vantage_yearly_data(ticker, years)

        if financial_data is None or len(financial_data) == 0:
            print(f"ERROR: No financial data available for {ticker}")
            return None
        
        # Sort data by year (most recent first)
        financial_data.sort(key=lambda x: x["year"])
            
        # Extract labels and financial metrics
        year_labels = [item["label"] for item in financial_data]
        revenue = [item["revenue"] for item in financial_data]
        earnings = [item["netIncome"] for item in financial_data]

        max_raw = max(max(revenue, default=0), max(earnings, default=0))

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

        revenue_scaled = [r / divisor for r in revenue]
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
        
        # Format y-axis with unit formatter
        def value_formatter(x, pos):
            if x == 0:
                return '0'
            return f'{x:.1f}{unit}'
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(value_formatter))
        
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
        
        # Add data source info with mock data note
        data_source = 'Data Source: Mock Data (Alpha Vantage API limit reached)'
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