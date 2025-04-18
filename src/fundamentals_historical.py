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
from matplotlib.lines import Line2D

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
            
            ticker_response = requests.get(ticker_url, timeout=10)
            
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
            
            # Get multiple years of financial data
            # Request more records than needed to ensure we get enough annual reports
            limit = min(25, years * 5)  
            financials_url = f"https://api.polygon.io/vX/reference/financials?ticker={ticker}&limit={limit}&apiKey={POLYGON_API_KEY}"
            
            financials_response = requests.get(financials_url, timeout=15)  # Increased timeout
            
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
                if report.get("fiscal_period") == "FY"
            ]
            
            # If we don't have enough annual reports, include quarterly reports for most recent years
            if len(annual_reports) < years:
                
                # Get unique years from available reports
                all_years = set(report.get("fiscal_year") for report in financials_data["results"] 
                               if report.get("fiscal_year"))
                
                # For each year that doesn't have an annual report, try to find Q4 reports
                for year in all_years:
                    if not any(report.get("fiscal_year") == year and report.get("fiscal_period") == "FY" 
                              for report in annual_reports):
                        # Look for Q4 report for this year
                        q4_reports = [
                            report for report in financials_data["results"]
                            if report.get("fiscal_year") == year and report.get("fiscal_period") == "Q4"
                        ]
                        if q4_reports:
                            annual_reports.extend(q4_reports)
            
            # If still not enough, add Q3, then Q2, then Q1
            if len(annual_reports) < years:
                for quarter in ["Q3", "Q2", "Q1"]:
                    if len(annual_reports) >= years:
                        break
                        
                    for year in all_years:
                        if not any(report.get("fiscal_year") == year for report in annual_reports):
                            q_reports = [
                                report for report in financials_data["results"]
                                if report.get("fiscal_year") == year and report.get("fiscal_period") == quarter
                            ]
                            if q_reports:
                                annual_reports.extend(q_reports)
            
            # Sort by fiscal year (most recent first for processing, will be reversed in chart)
            annual_reports.sort(key=lambda x: (x.get("fiscal_year", "0"), 
                                              {"FY": 5, "Q4": 4, "Q3": 3, "Q2": 2, "Q1": 1}.get(x.get("fiscal_period", ""), 0)), 
                               reverse=True)
            
            # Limit to requested number of years
            annual_reports = annual_reports[:years]
            
            
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
                        
                        # Extract revenue - check multiple possible fields
                        revenue = 0
                        for revenue_field in ["revenues", "revenue", "total_revenue", "totalRevenue"]:
                            if revenue_field in income_stmt:
                                try:
                                    revenue = float(income_stmt[revenue_field].get("value", 0))
                                    if revenue > 0:
                                        break
                                except (ValueError, TypeError):
                                    continue
                        
                        # Extract net income - check multiple possible fields
                        net_income = 0
                        for income_field in ["net_income_loss", "netIncome", "net_income", "profit"]:
                            if income_field in income_stmt:
                                try:
                                    net_income = float(income_stmt[income_field].get("value", 0))
                                    break
                                except (ValueError, TypeError):
                                    continue
                        
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
                print(f"INFO: Successfully processed {len(processed_data)} financial reports")
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
        financial_data, company_name = get_polygon_yearly_data(ticker, years)
        if financial_data is None or len(financial_data) == 0:
            print(f"ERROR: No financial data available for {ticker}, falling back to mock data")
            financial_data, company_name = generate_mock_financial_data(ticker, years)
            if financial_data is None or len(financial_data) == 0:
                print(f"ERROR: Failed to generate mock data for {ticker}")
                return None
        
        # Sort data by year (chronological order - oldest to newest)
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
            divisor, unit = 1,    ''           # Ones
            
        revenue_scaled = [r / divisor for r in revenue]
        earnings_scaled = [e / divisor for e in earnings]
        
        if dark_theme:
            plt.style.use('dark_background')
            bar_colours = ['#4682B4', '#66BB6A']  
            line_colours = ['#57a0ff', '#ffdf8e'] 
            text_colour = 'white'
            grid_colour = '#555555'
        else:
            plt.style.use('default')
            bar_colours = ['#4682B4', '#66BB6A'] 
            line_colours = ['#6e99c7', '#f4ae5b']
            text_colour = 'black'
            grid_colour = '#cccccc'
        
        # Create the figure and axes
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Bar positions and width
        bar_width = 0.35
        x = np.arange(len(year_labels))
        
        # Create bars
        revenue_bars = ax.bar(x - bar_width/2, revenue_scaled, bar_width, color=bar_colours[0])
        earnings_bars = ax.bar(x + bar_width/2, earnings_scaled, bar_width, color=bar_colours[1])
        
        # Create a second axis for the trend lines that's aligned with the first
        ax2 = ax.twinx() 
        ax2.set_ylim(ax.get_ylim())  
        ax2.spines['right'].set_visible(False)  
        ax2.spines['top'].set_visible(False)    
        ax2.yaxis.set_visible(False)
        
        # Get top of each bar for line plotting (to place lines at the exact top)
        revenue_tops = revenue_scaled.copy()
        earnings_tops = earnings_scaled.copy()
        
        # Add lines for revenue and earnings trends with markers at the top of each bar
        revenue_line = ax2.plot(x - bar_width/2, revenue_tops, '-o', color=line_colours[0], 
                               linewidth=2.5, markersize=6, zorder=10)
        earnings_line = ax2.plot(x + bar_width/2, earnings_tops, '-o', color=line_colours[1], 
                                linewidth=2.5, markersize=6, zorder=10)
        
        # Set title with company name
        chart_title = f'{company_name}: Annual Revenue vs. Earnings (YOY)'
        ax.set_title(chart_title, fontsize=22, pad=20, color=text_colour, fontweight='bold')
        
        # Latest values for the legend
        latest_revenue = revenue_scaled[-1]
        latest_earnings = earnings_scaled[-1]
        
        # Create a special legend at the top of the figure
        # First, clear any auto-generated legends
        if ax.get_legend():
            ax.get_legend().remove()
            
        
        # Format revenue and earnings values
        revenue_text = f"{latest_revenue:.1f}{unit}"
        earnings_text = f"{latest_earnings:.1f}{unit}"
        
        # Calculate the width needed for each part 
        # Using a fixed-width approach for the legend items
        legend_elements = [
            # Revenue box and label
            Line2D([0], [0], color='none', marker='s', markersize=15, 
                   markerfacecolor=bar_colours[0], label="Revenue"),
            # Revenue value (with spacing)
            Line2D([0], [0], color='none', marker=' ', markersize=1, 
                   label=revenue_text),
            # Spacer
            Line2D([0], [0], color='none', marker=' ', markersize=1, 
                   label="          "),
            # Earnings box and label
            Line2D([0], [0], color='none', marker='s', markersize=15, 
                   markerfacecolor=bar_colours[1], label="Earnings"),
            # Earnings value with spacing
            Line2D([0], [0], color='none', marker=' ', markersize=1, 
                   label=earnings_text)
        ]
        
        # Place legend at the top of the plot
        legend = ax.legend(handles=legend_elements, loc='upper center', 
                          ncol=5, frameon=False, fontsize=14,
                          bbox_to_anchor=(0.5, 1.05))
        
        # Make the value texts bold
        for i, text in enumerate(legend.get_texts()):
            if i == 1 or i == 4:  # Revenue and earnings values
                text.set_fontweight('bold')
                
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
        ax.grid(axis='y', linestyle='--', alpha=0.3, color=grid_colour)
        
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
                   transform=fig.transFigure, fontsize=8, alpha=0.7, color=text_colour)
        
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to base64
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        print("INFO: Chart generated successfully")
        return img_str
    
    except Exception as e:
        print(f"ERROR: Failed to generate chart: {e}")
        print(traceback.format_exc())
        return None



