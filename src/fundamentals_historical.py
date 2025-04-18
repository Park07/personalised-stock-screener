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


def get_fmp_cashflow_data(ticker, years=4, retries=3):
    """Get free cash flow data from Financial Modeling Prep API with retries"""
    print(f"INFO: Fetching cash flow data for {ticker} from FMP")
    
    # You should store your FMP API key in config.py similar to POLYGON_API_KEY
    FMP_API_KEY = os.getenv("FMP_API_KEY")
    if not FMP_API_KEY:
        print("ERROR: Financial Modeling Prep API key not found")
        return None, ticker
    
    for attempt in range(retries):
        try:
            # Fetch company name first
            company_info_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={FMP_API_KEY}"
            company_response = requests.get(company_info_url, timeout=10)
            
            company_name = ticker
            if company_response.status_code == 200:
                company_data = company_response.json()
                if company_data and len(company_data) > 0:
                    company_name = company_data[0].get("companyName", ticker)
                    print(f"INFO: Company name: {company_name}")
            
            # Get cash flow statement data
            cashflow_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&apikey={FMP_API_KEY}"
            print(f"DEBUG: Fetching cash flow data from FMP (attempt {attempt+1}/{retries})")
            
            cashflow_response = requests.get(cashflow_url, timeout=15)
            print(f"DEBUG: Cash flow API status: {cashflow_response.status_code}")
            
            if cashflow_response.status_code != 200:
                print(f"WARNING: Failed to fetch cash flow data, status: {cashflow_response.status_code}")
                if attempt < retries - 1:
                    print(f"INFO: Waiting 2 seconds before retrying...")
                    time.sleep(2)
                    continue
                return None, company_name
            
            cashflow_data = cashflow_response.json()
            
            if not cashflow_data:
                print(f"WARNING: No cash flow data available in FMP response")
                if attempt < retries - 1:
                    print(f"INFO: Waiting 2 seconds before retrying...")
                    time.sleep(2)
                    continue
                return None, company_name
                
            # Limit to requested number of years
            limited_data = cashflow_data[:years]
            
            print(f"DEBUG: Retrieved {len(limited_data)} cash flow statements")
            
            # Process the cash flow data
            processed_data = []
            
            for statement in limited_data:
                try:
                    # Extract date and format fiscal year
                    date_str = statement.get("date", "")
                    if date_str:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        fiscal_year = date_obj.year
                        year_label = f"FY{fiscal_year}"
                    else:
                        # If date is missing, use calendarYear if available
                        fiscal_year = int(statement.get("calendarYear", 0))
                        year_label = f"FY{fiscal_year}"
                    
                    # Extract FCF directly
                    free_cash_flow = statement.get("freeCashFlow", 0)
                    
                    # If FCF not available, calculate from components
                    if not free_cash_flow:
                        operating_cash_flow = statement.get("operatingCashFlow", 0) or statement.get("netCashProvidedByOperatingActivities", 0)
                        capital_expenditure = statement.get("capitalExpenditure", 0) or statement.get("investmentsInPropertyPlantAndEquipment", 0)
                        
                        # Capital expenditure is typically negative in FMP data
                        if capital_expenditure < 0:
                            capital_expenditure = abs(capital_expenditure)
                            
                        if operating_cash_flow and capital_expenditure:
                            free_cash_flow = operating_cash_flow - capital_expenditure
                    
                    print(f"INFO: {year_label}, FCF: ${free_cash_flow/1e9:.2f}B")
                    
                    processed_data.append({
                        "year": fiscal_year,
                        "label": year_label,
                        "freeCashFlow": free_cash_flow
                    })
                    
                except Exception as e:
                    print(f"WARNING: Error processing cash flow statement: {e}")
                    continue
            
            # Check if we have any data
            if processed_data:
                # Sort by year (oldest to newest)
                processed_data.sort(key=lambda x: x["year"])
                print(f"INFO: Successfully processed {len(processed_data)} cash flow statements")
                return processed_data, company_name
            else:
                print("WARNING: No processable cash flow data found in response")
                if attempt < retries - 1:
                    continue
                return None, company_name
            
        except Exception as e:
            print(f"ERROR: Failed to fetch FMP cash flow data (attempt {attempt+1}/{retries}): {e}")
            print(traceback.format_exc())
            if attempt < retries - 1:
                print(f"INFO: Waiting 3 seconds before retrying...")
                time.sleep(3)
            else:
                return None, ticker
    
    print("ERROR: All retry attempts failed")
    return None, ticker

def generate_free_cash_flow_chart(ticker, years=4, dark_theme=True):
    """Generate a chart showing free cash flow trend over time."""
    print(f"INFO: Generating FCF chart for {ticker}, years={years}, dark_theme={dark_theme}")
    
    try:
        # Get data from FMP API
        financial_data, company_name = get_fmp_cashflow_data(ticker, years)
        if financial_data is None or len(financial_data) == 0:
            print(f"ERROR: No financial data available for {ticker}")
            return None
        
        # Extract labels and metrics
        year_labels = [item["label"] for item in financial_data]
        free_cash_flow = [item["freeCashFlow"] for item in financial_data]
        
        # Scale values for display
        max_raw = max(free_cash_flow, default=0)
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
            
        fcf_scaled = [f / divisor for f in free_cash_flow]
        
        # Setup chart theme
        if dark_theme:
            plt.style.use('dark_background')
            bar_color = '#4daf4a'      # Green 
            line_color = '#72cf70'     # Lighter green for trend line
            text_color = 'white'
            grid_color = '#555555'
        else:
            plt.style.use('default')
            bar_color = '#4daf4a'      # Green 
            line_color = '#72cf70'     # Lighter green for trend line
            text_color = 'black'
            grid_color = '#cccccc'
            
        # Create the chart  
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Bar positions
        x = np.arange(len(year_labels))
        
        # Create bars with a wider width since we only have one series
        fcf_bars = ax.bar(x, fcf_scaled, 0.7, color=bar_color)
        
        # Add trend line
        ax2 = ax.twinx() 
        ax2.set_ylim(ax.get_ylim())
        ax2.spines['right'].set_visible(False)  
        ax2.spines['top'].set_visible(False)    
        ax2.yaxis.set_visible(False)
        
        # Draw trend line at the top of each bar
        ax2.plot(x, fcf_scaled, '-o', color=line_color, 
                linewidth=2.5, markersize=6, zorder=10)
        
        # Calculate year-over-year growth rates for annotation
        growth_rates = []
        for i in range(1, len(fcf_scaled)):
            if fcf_scaled[i-1] > 0:
                growth = (fcf_scaled[i] - fcf_scaled[i-1]) / fcf_scaled[i-1] * 100
                growth_rates.append(growth)
            else:
                growth_rates.append(0)
        
        # Add growth rate annotations above bars (except first bar)
        for i in range(1, len(fcf_scaled)):
            if i-1 < len(growth_rates):
                growth = growth_rates[i-1]
                color = '#4daf4a' if growth >= 0 else '#e41a1c' 
                ax.annotate(f"{growth:.1f}%", 
                            xy=(x[i], fcf_scaled[i]), 
                            xytext=(0, 10),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            color=color, 
                            fontweight='bold',
                            fontsize=10)
        
        # Set title and labels
        chart_title = f'{company_name}: Free Cash Flow Trend'
        ax.set_title(chart_title, fontsize=22, pad=20, color=text_color, fontweight='bold')
        
        # Create custom legend with latest FCF value
        latest_fcf = fcf_scaled[-1]
        
        legend_elements = [
            # FCF square and label
            Line2D([0], [0], color='none', marker='s', markersize=15, 
                   markerfacecolor=bar_color, label="Free Cash Flow"),
            # FCF value
            Line2D([0], [0], color='none', marker=' ', markersize=1, 
                   label=f"{latest_fcf:.1f}{unit}")
        ]
        
        legend = ax.legend(handles=legend_elements, loc='upper left', 
                          ncol=2, frameon=False, fontsize=14)
        
        # Make the value bold
        legend.get_texts()[1].set_fontweight('bold')
        
        # Calculate and display CAGR (Compound Annual Growth Rate)
        if len(fcf_scaled) > 1 and fcf_scaled[0] > 0:
            years_count = len(fcf_scaled) - 1
            cagr = ((fcf_scaled[-1] / fcf_scaled[0]) ** (1 / years_count) - 1) * 100
            cagr_text = f"CAGR: {cagr:.1f}%"
            ax.text(0.02, 0.95, cagr_text, transform=ax.transAxes, 
                    fontsize=12, va='top', color=text_color)
                
        # Configure axes  
        ax.set_xticks(x)
        ax.set_xticklabels(year_labels, fontsize=12)
        
        def value_formatter(x, pos):
            if x == 0:
                return '0'
            return f'{x:.1f}{unit}'
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(value_formatter))
        
        # Add grid and finalize
        ax.grid(axis='y', linestyle='--', alpha=0.3, color=grid_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Data source
        data_source = 'Data Source: Financial Modeling Prep'
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
        
        print("INFO: FCF chart generated successfully")
        return img_str
        
    except Exception as e:
        print(f"ERROR: Failed to generate FCF chart: {e}")
        print(traceback.format_exc())
        return None
