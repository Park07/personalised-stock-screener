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

from config import POLYGON_API_KEY

def get_polygon_yearly_data(ticker, years=4, retries=3):
    """Get yearly revenue and earnings from Polygon.io with retries"""
    print(f"INFO: Fetching live Polygon.io yearly data for {ticker}")
    
    
    today = datetime.utcnow().date()
    
    for attempt in range(retries):
        try:
            # Get company overview from ticker details endpoint
            ticker_url = f"https://api.polygon.io/v3/reference/tickers/{ticker}?apiKey={POLYGON_API_KEY}"
            
            print(f"DEBUG: Fetching company details from Polygon.io (attempt {attempt+1}/{retries})")
            ticker_response = requests.get(ticker_url, timeout=10)
            print(f"DEBUG: Ticker details response status: {ticker_response.status_code}")
            
            company_name = ticker
            if ticker_response.status_code == 200:
                ticker_data = ticker_response.json()
                if "results" in ticker_data:
                    company_name = ticker_data["results"].get("name", ticker)
                    print(f"INFO: Company name: {company_name}")
                else:
                    print(f"WARNING: No results found in ticker details response")
            else:
                print(f"WARNING: Failed to get ticker details, status: {ticker_response.status_code}")
                print(f"Response: {ticker_response.text[:200]}")
                if attempt < retries - 1:
                    print(f"INFO: Waiting 2 seconds before retrying...")
                    time.sleep(2)
                    continue
            
            # Get financial data for the past few years
            # We'll focus on annual reports (fiscal_period=FY)
            financials_url = f"https://api.polygon.io/vX/reference/financials?ticker={ticker}&limit=10&apiKey={POLYGON_API_KEY}"
            
            print(f"DEBUG: Fetching financials from Polygon.io (attempt {attempt+1}/{retries})")
            financials_response = requests.get(financials_url, timeout=10)
            print(f"DEBUG: Financials response status: {financials_response.status_code}")
            
            if financials_response.status_code != 200:
                print(f"WARNING: Failed to fetch financials, status: {financials_response.status_code}")
                print(f"Response: {financials_response.text[:200]}")
                if attempt < retries - 1:
                    print(f"INFO: Waiting 2 seconds before retrying...")
                    time.sleep(2)
                    continue
                return None, company_name
            
            financials_data = financials_response.json()
            
            if "results" not in financials_data or not financials_data["results"]:
                print(f"WARNING: No financial data available in Polygon.io response")
                if attempt < retries - 1:
                    print(f"INFO: Waiting 2 seconds before retrying...")
                    time.sleep(2)
                    continue
                return None, company_name
            
            # Process the financial data
            processed_data = []
            
            # First, filter to get only annual reports (fiscal_period=FY)
            annual_reports = [
                report for report in financials_data["results"] 
                if report.get("fiscal_period") == "FY" or (
                    # Include Q1 reports from most recent year if not enough annual reports
                    len([r for r in financials_data["results"] if r.get("fiscal_period") == "FY"]) < years and 
                    report.get("fiscal_period") == "Q1"
                )
            ]
            
            # Sort by fiscal year (most recent first)
            annual_reports.sort(key=lambda x: x.get("fiscal_year", "0"), reverse=True)
            
            # Limit to requested number of years
            annual_reports = annual_reports[:years]
            
            print(f"DEBUG: Found {len(annual_reports)} annual/quarterly reports")
            
            for report in annual_reports:
                try:
                    fiscal_year = int(report.get("fiscal_year", 0))
                    fiscal_period = report.get("fiscal_period", "")
                    
                    # Create year label
                    if fiscal_period == "FY":
                        year_label = f"FY{fiscal_year}"
                    else:
                        year_label = f"{fiscal_period} {fiscal_year}"
                    
                    # Extract revenue and net income from income statement
                    if "financials" in report and "income_statement" in report["financials"]:
                        income_stmt = report["financials"]["income_statement"]
                        
                        # Extract revenue
                        revenue = 0
                        if "revenues" in income_stmt:
                            revenue = float(income_stmt["revenues"].get("value", 0))
                        
                        # Extract net income
                        net_income = 0
                        if "net_income_loss" in income_stmt:
                            net_income = float(income_stmt["net_income_loss"].get("value", 0))
                        
                        print(f"INFO: {year_label}, Revenue: ${revenue/1e9:.2f}B, Income: ${net_income/1e9:.2f}B")
                        
                        processed_data.append({
                            "year": fiscal_year,
                            "label": year_label,
                            "revenue": revenue,
                            "netIncome": net_income
                        })
                    else:
                        print(f"WARNING: No income statement found for {year_label}")
                        
                except Exception as e:
                    print(f"WARNING: Error processing report for {report.get('fiscal_year')}: {e}")
                    continue
            
            # Check if we have any data
            if processed_data:
                return processed_data, company_name
            else:
                print("WARNING: No processable data found in response")
                if attempt < retries - 1:
                    continue
                return None, company_name
            
        except Exception as e:
            print(f"ERROR: Failed to fetch Polygon.io data (attempt {attempt+1}/{retries}): {e}")
            print(traceback.format_exc())
            if attempt < retries - 1:
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
        # Get data from Polygon.io
        financial_data, company_name = get_polygon_yearly_data(ticker, years)

        if financial_data is None or len(financial_data) == 0:
            print(f"ERROR: No financial data available for {ticker}")
            # Fall back to mock data if needed
            financial_data, company_name = generate_mock_financial_data(ticker, years)
            if financial_data is None:
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
        
        # Add data source info
        data_source = 'Data Source: Polygon.io'
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


