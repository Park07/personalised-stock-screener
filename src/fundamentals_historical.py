import base64
import io
import json
import os
import random
import time
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, Response
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import requests

from config import POLYGON_API_KEY, FMP_API_KEY

app = Flask(__name__)

BASE_URL = "https://financialmodelingprep.com/api/v3/"
POLYGON_BASE_URL = "https://api.polygon.io/"


def get_company_name(ticker, retries=3):
    """Get company name from ticker details endpoint with retries."""
    for attempt in range(retries):
        try:
            ticker_url = (
                f"{POLYGON_BASE_URL}/v3/reference/tickers/{ticker}"
                f"?apiKey={POLYGON_API_KEY}"
            )
            ticker_response = requests.get(ticker_url, timeout=10)

            if ticker_response.status_code == 200:
                ticker_data = ticker_response.json()
                if "results" in ticker_data:
                    return ticker_data["results"].get("name", ticker)
            else:
                print(ticker_response.text[:200])
                if attempt < retries - 1:
                    print("INFO: Waiting 2 seconds before retrying...")
                    time.sleep(2)
        except Exception:
            print(traceback.format_exc())
            if attempt < retries - 1:
                time.sleep(2)
    return ticker  # Return ticker as fallback if company name can't be retrieved


def fetch_financial_data(ticker, limit, retries=3):
    """Fetch financial data from Polygon API with retries."""
    for attempt in range(retries):
        try:
            financials_url = (
                f"{POLYGON_BASE_URL}vX/reference/financials?"
                f"ticker={ticker}&limit={limit}&apiKey={POLYGON_API_KEY}"
            )
            financials_response = requests.get(financials_url, timeout=15)

            if financials_response.status_code == 200:
                financials_data = financials_response.json()
                if "results" in financials_data and financials_data["results"]:
                    return financials_data["results"]
            else:
                print(financials_response.text[:200])
            if attempt < retries - 1:
                print("INFO: Waiting 2 seconds before retrying...")
                time.sleep(2)
        except Exception:
            print(traceback.format_exc())
            if attempt < retries - 1:
                time.sleep(3)
    return None


def filter_annual_reports(financial_results, years):
    """Filter and organize annual reports, adding quarterly reports if needed."""
    # Filter only annual reports (fiscal_period=FY)
    annual_reports = [
        report
        for report in financial_results
        if report.get("fiscal_period") == "FY"
    ]

    # If not enough annual reports, include Q4 for missing years
    if len(annual_reports) < years:
        all_years = {
            report.get("fiscal_year")
            for report in financial_results
            if report.get("fiscal_year")
        }
        for year in all_years:
            if not any(
                r.get("fiscal_year") == year
                and r.get("fiscal_period") == "FY"
                for r in annual_reports
            ):
                q4_reports = [
                    r
                    for r in financial_results
                    if (
                        r.get("fiscal_year") == year
                        and r.get("fiscal_period") == "Q4"
                    )
                ]
                if q4_reports:
                    annual_reports.extend(q4_reports)

    # Then add Q3, Q2, Q1 if still needed
    if len(annual_reports) < years:
        for quarter in ["Q3", "Q2", "Q1"]:
            if len(annual_reports) >= years:
                break
            for year in all_years:
                if not any(
                    r.get("fiscal_year") == year
                    for r in annual_reports
                ):
                    q_reports = [
                        r
                        for r in financial_results
                        if (
                            r.get("fiscal_year") == year
                            and r.get("fiscal_period") == quarter
                        )
                    ]
                    if q_reports:
                        annual_reports.extend(q_reports)

    # Sort and limit to requested years
    annual_reports.sort(
        key=lambda x: (
            x.get("fiscal_year", "0"),
            {
                "FY": 5,
                "Q4": 4,
                "Q3": 3,
                "Q2": 2,
                "Q1": 1,
            }.get(x.get("fiscal_period", ""), 0),
        ),
        reverse=True,
    )
    return annual_reports[:years]


def extract_financial_value(income_statement, field_names):
    """Extract financial value from income statement using multiple possible field names."""
    for field in field_names:
        if field in income_statement:
            try:
                value = income_statement[field].get("value", 0)
                return float(value)
            except (ValueError, TypeError):
                continue
    return 0


def process_annual_report(report):
    """Process a single annual report to extract year, revenue, and net income."""
    try:
        fy = int(report.get("fiscal_year", 0))
        fp = report.get("fiscal_period", "")
        if fp == "FY":
            year_label = f"FY{fy}"
        else:
            year_label = f"{fp} {fy}"

        if "financials" in report and "income_statement" in report["financials"]:
            income = report["financials"]["income_statement"]

            # Extract revenue
            revenue = extract_financial_value(
                income,
                ["revenues", "revenue", "total_revenue", "totalRevenue"]
            )

            # Extract net income
            net_income = extract_financial_value(
                income,
                ["net_income_loss", "netIncome", "net_income", "profit"]
            )

            print(
                f"INFO: {year_label}, "
                f"Revenue: ${revenue / 1e9:.2f}B, "
                f"Income: ${net_income / 1e9:.2f}B"
            )

            return {
                "year": fy,
                "label": year_label,
                "revenue": revenue,
                "netIncome": net_income,
            }

    except Exception:
        # Skip this report if parsing fails
        return None


def get_polygon_yearly_data(ticker, years=4, retries=3):
    """Get yearly revenue and earnings from Polygon.io with retries"""
    print(f"INFO: Fetching live Polygon.io yearly data for {ticker}")
    # Get company name
    company_name = get_company_name(ticker, retries)
    # Get financial data
    limit = min(25, years * 5)
    financial_results = fetch_financial_data(ticker, limit, retries)
    if financial_results is None:
        return None, company_name
    # Filter annual reports
    annual_reports = filter_annual_reports(financial_results, years)
    # Process reports
    processed_data = []
    for report in annual_reports:
        report_data = process_annual_report(report)
        if report_data:
            processed_data.append(report_data)
    if processed_data:
        return processed_data, company_name
    return None, company_name


def prepare_chart_data(financial_data):
    """Prepare data for yearly performance chart"""
    # Sort data by year (chronological order - oldest to newest)
    financial_data.sort(key=lambda x: x["year"])

    # Extract labels and financial metrics
    year_labels = [item["label"] for item in financial_data]
    revenue = [item["revenue"] for item in financial_data]
    earnings = [item["netIncome"] for item in financial_data]

    # Get maximum values
    revenue_max = max(revenue, default=0)
    earnings_max = max(earnings, default=0)
    max_raw = max(revenue_max, earnings_max)

    # Determine appropriate scale
    if max_raw >= 1e12:
        divisor, unit = 1e12, 'T'          # Trillions
    elif max_raw >= 1e9:
        divisor, unit = 1e9, 'B'          # Billions
    elif max_raw >= 1e6:
        divisor, unit = 1e6, 'M'          # Millions
    elif max_raw >= 1e3:
        divisor, unit = 1e3, 'K'          # Thousands
    else:
        divisor, unit = 1, ''           # Ones

    # Scale the data
    revenue_scaled = [r / divisor for r in revenue]
    earnings_scaled = [e / divisor for e in earnings]

    return year_labels, revenue_scaled, earnings_scaled, divisor, unit


def setup_chart_theme(dark_theme):
    """Setup chart colors based on theme"""
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

    return bar_colours, line_colours, text_colour, grid_colour


def create_bars_and_lines(
        ax,
        x,
        revenue_scaled,
        earnings_scaled,
        bar_colours,
        line_colours):
    """Create bars and trend lines on chart"""
    # Bar width
    bar_width = 0.35

    # Create bars
    _revenue_bars = ax.bar(
        x - bar_width / 2,
        revenue_scaled,
        bar_width,
        color=bar_colours[0])
    _earnings_bars = ax.bar(
        x + bar_width / 2,
        earnings_scaled,
        bar_width,
        color=bar_colours[1])

    # Create a second axis for the trend lines that's aligned with the first
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    ax2.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax2.yaxis.set_visible(False)

    # Add lines for revenue and earnings trends with markers at the top of
    # each bar
    _revenue_line = ax2.plot(
        x - bar_width / 2,
        revenue_scaled,
        '-o',
        color=line_colours[0],
        linewidth=2.5,
        markersize=6,
        zorder=10)
    _earnings_line = ax2.plot(
        x + bar_width / 2,
        earnings_scaled,
        '-o',
        color=line_colours[1],
        linewidth=2.5,
        markersize=6,
        zorder=10)

    return ax2


def setup_legend(ax, bar_colours, revenue_scaled, earnings_scaled, unit):
    """Setup chart legend"""
    # Latest values for the legend
    latest_revenue = revenue_scaled[-1]
    latest_earnings = earnings_scaled[-1]

    # Remove existing legend if present
    if ax.get_legend():
        ax.get_legend().remove()

    # Format revenue and earnings values
    revenue_text = f"{latest_revenue:.1f}{unit}"
    earnings_text = f"{latest_earnings:.1f}{unit}"

    # Create legend elements
    legend_elements = [
        # Revenue box and label
        Line2D([0], [0], color='none', marker='s', markersize=15,
               markerfacecolor=bar_colours[0], label="Revenue"),
        # Revenue value
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
        if i in (1, 4):  # Revenue and earnings values
            text.set_fontweight('bold')

    return legend


def configure_axes(
        ax,
        x,
        year_labels,
        revenue_scaled,
        earnings_scaled,
        unit,
        _text_colour,
        grid_colour,
        dark_theme):
    """Configure chart axes"""
    # Set x-axis ticks and labels
    ax.set_xticks(x)
    ax.set_xticklabels(year_labels, fontsize=12)

    # Format y-axis
    def value_formatter(x, _pos):
        if x == 0:
            return '0'
        return f'{x:.1f}{unit}'

    ax.yaxis.set_major_formatter(plt.FuncFormatter(value_formatter))
    ax.grid(axis='y', linestyle='--', alpha=0.3, color=grid_colour)

    # Remove unnecessary spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    if dark_theme:
        ax.spines['bottom'].set_color('#555555')
        ax.spines['left'].set_color('#555555')

    # Configure y-axis ticks with nice steps
    max_value = max(
        revenue_scaled + earnings_scaled,
        default=0
    )

    if max_value > 0:
        step = max_value / 5
        magnitude = 10 ** np.floor(np.log10(step))
        step = np.ceil(step / magnitude) * magnitude
        y_ticks = np.arange(0, max_value + step, step)
        ax.set_yticks(y_ticks)


def generate_yearly_performance_chart(ticker, years=4, dark_theme=True):
    """Generate a yearly performance chart comparing revenue and earnings."""
    try:
        financial_data, company_name = get_polygon_yearly_data(ticker, years)
        if financial_data is None or len(financial_data) == 0:
            return None

        # Prepare chart data
        year_labels, revenue_scaled, earnings_scaled, _divisor, unit = prepare_chart_data(
            financial_data)

        # Setup chart theme
        bar_colours, line_colours, text_colour, grid_colour = setup_chart_theme(
            dark_theme)

        # Create the figure and axes
        fig, ax = plt.subplots(figsize=(10, 6))

        # Bar positions
        x = np.arange(len(year_labels))

        # Create bars and trend lines
        _ax2 = create_bars_and_lines(
            ax,
            x,
            revenue_scaled,
            earnings_scaled,
            bar_colours,
            line_colours)

        # Set title with company name
        chart_title = f'{company_name}: Annual Revenue vs. Earnings (YOY)'
        ax.set_title(
            chart_title,
            fontsize=22,
            pad=20,
            color=text_colour,
            fontweight='bold')

        # Setup legend
        _legend = setup_legend(
            ax,
            bar_colours,
            revenue_scaled,
            earnings_scaled,
            unit)
        # Configure axes
        configure_axes(
            ax,
            x,
            year_labels,
            revenue_scaled,
            earnings_scaled,
            unit,
            text_colour,
            grid_colour,
            dark_theme)

        # Add data source info
        data_source = 'Data Source: Polygon.io'
        if data_source:
            ax.text(
                0.99,
                0.01,
                data_source,
                ha='right',
                va='bottom',
                transform=fig.transFigure,
                fontsize=8,
                alpha=0.7,
                color=text_colour)
        plt.tight_layout()
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        # Convert to base64
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        return img_str

    except Exception as _e:
        print(traceback.format_exc())
        return None


def get_company_info(ticker, retries=3):
    """Fetch company name from FMP API"""
    for attempt in range(retries):
        try:
            company_info_url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
            company_response = requests.get(company_info_url, timeout=10)
            company_name = ticker
            if company_response.status_code == 200:
                company_data = company_response.json()
                if company_data and len(company_data) > 0:
                    company_name = company_data[0].get("companyName", ticker)
                    print(f"INFO: Company name: {company_name}")
            return company_name
        except Exception as e:
            print(
                f"ERROR: Failed to fetch company info (attempt {
                    attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return ticker


def fetch_cashflow_data(ticker, retries=3):
    """Fetch cashflow data from FMP API"""
    for attempt in range(retries):
        try:
            cashflow_url = (
                f"{BASE_URL}/cash-flow-statement/{ticker}"
                f"?period=annual&apikey={FMP_API_KEY}"
            )
            cashflow_response = requests.get(cashflow_url, timeout=15)
            if cashflow_response.status_code != 200:
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return None
            cashflow_data = cashflow_response.json()
            if not cashflow_data:
                print(f"WARNING: No cash flow data available in FMP response")
                if attempt < retries - 1:
                    print(f"INFO: Waiting 2 seconds before retrying...")
                    time.sleep(2)
                    continue
                return None
            return cashflow_data
        except Exception as e:
            print(
                f"ERROR: Failed to fetch FMP cash flow data (attempt {
                    attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"INFO: Waiting 3 seconds before retrying...")
                time.sleep(3)
    return None


def process_cashflow_statement(statement):
    """Process a single cashflow statement"""
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
            operating_cash_flow = (
                statement.get("operatingCashFlow", 0)
                or statement.get("netCashProvidedByOperatingActivities", 0)
            )
            capital_expenditure = (
                statement.get("capitalExpenditure", 0)
                or statement.get("investmentsInPropertyPlantAndEquipment", 0)
            )
            # Capital expenditure is typically negative in FMP data
            if capital_expenditure < 0:
                capital_expenditure = abs(capital_expenditure)
            if operating_cash_flow and capital_expenditure:
                free_cash_flow = operating_cash_flow - capital_expenditure
        print(f"INFO: {year_label}, FCF: ${free_cash_flow / 1e9:.2f}B")

        return {
            "year": fiscal_year,
            "label": year_label,
            "freeCashFlow": free_cash_flow
        }
    except Exception as e:
        print(f"WARNING: Error processing cash flow statement: {e}")
        return None


def get_fmp_cashflow_data(ticker, years=4, retries=3):
    """Get free cash flow data from Financial Modeling Prep API with retries"""
    # Fetch company name
    company_name = get_company_info(ticker, retries)
    # Fetch cashflow data
    cashflow_data = fetch_cashflow_data(ticker, retries)
    if cashflow_data is None:
        return None, company_name

    # Limit to requested number of years
    limited_data = cashflow_data[:years]

    # Process the cash flow data
    processed_data = []
    for statement in limited_data:
        result = process_cashflow_statement(statement)
        if result:
            processed_data.append(result)

    # Check if we have any data
    if processed_data:
        # Sort by year (oldest to newest)
        processed_data.sort(key=lambda x: x["year"])
        print(
            f"INFO: Successfully processed {
                len(processed_data)} cash flow statements")
        return processed_data, company_name

    return None, company_name


def prepare_fcf_data(financial_data):
    """Extract and scale free cash flow data"""
    # Extract labels and metrics
    year_labels = [item["label"] for item in financial_data]
    free_cash_flow = [item["freeCashFlow"] for item in financial_data]

    # Scale values for display
    max_raw = max(free_cash_flow, default=0)
    if max_raw >= 1e12:
        divisor, unit = 1e12, 'T'          # Trillions
    elif max_raw >= 1e9:
        divisor, unit = 1e9, 'B'          # Billions
    elif max_raw >= 1e6:
        divisor, unit = 1e6, 'M'          # Millions
    elif max_raw >= 1e3:
        divisor, unit = 1e3, 'K'          # Thousands
    else:
        divisor, unit = 1, ''           # Ones
    fcf_scaled = [f / divisor for f in free_cash_flow]
    return year_labels, fcf_scaled, divisor, unit


def calculate_cagr(fcf_scaled):
    """Calculate CAGR for FCF data"""
    cagr = 0
    if len(fcf_scaled) > 1 and fcf_scaled[0] > 0:
        years_count = len(fcf_scaled) - 1
        cagr = ((fcf_scaled[-1] / fcf_scaled[0])
                ** (1 / years_count) - 1) * 100
    return cagr


def setup_fcf_chart_theme(dark_theme):
    """Setup chart colors based on theme"""
    if dark_theme:
        plt.style.use('dark_background')
        bar_color = '#4daf4a'      # Green for FCF
        line_color = '#72cf70'     # Lighter green for trend line
        text_color = 'white'
        grid_color = '#555555'
    else:
        plt.style.use('default')
        bar_color = '#4daf4a'      # Green for FCF
        line_color = '#72cf70'     # Lighter green for trend line
        text_color = 'black'
        grid_color = '#cccccc'
    return bar_color, line_color, text_color, grid_color


def create_fcf_bars_and_line(ax, x, fcf_scaled, bar_color, line_color):
    """Create FCF bars and trend line"""
    # Create bars with a wider width
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
    return fcf_bars, ax2


def add_growth_annotations(ax, x, fcf_scaled):
    """Add growth rate annotations to chart"""
    # Calculate year-over-year growth rates for annotation
    growth_rates = []
    for i in range(1, len(fcf_scaled)):
        if fcf_scaled[i - 1] > 0:
            growth = (fcf_scaled[i] - fcf_scaled[i - 1]) / \
                fcf_scaled[i - 1] * 100
            growth_rates.append(growth)
        else:
            growth_rates.append(0)
    # Add growth rate annotations above bars (except first bar)
    for i in range(1, len(fcf_scaled)):
        if i - 1 < len(growth_rates):
            growth = growth_rates[i - 1]
            # Green = positive, red = negative
            color = '#4daf4a' if growth >= 0 else '#e41a1c'
            ax.annotate(f"{growth:.1f}%",
                        xy=(x[i], fcf_scaled[i]),
                        xytext=(0, 14),  # Higher position
                        textcoords="offset points",
                        ha='center', va='bottom',
                        color=color,
                        fontweight='bold',
                        fontsize=10)
    # Add FCF value annotations ONLY INSIDE each bar
    for i, value in enumerate(fcf_scaled):
        ax.annotate(f"{value:.1f}{unit}",
                    xy=(x[i], value / 2),  # Position in middle of bar
                    ha='center', va='center',
                    color='white',
                    fontweight='bold',
                    fontsize=11)


def configure_fcf_axes(ax, x, year_labels, unit, grid_color):
    """Configure chart axes"""
    # Configure axes
    ax.set_xticks(x)
    ax.set_xticklabels(year_labels, fontsize=12)

    def value_formatter(x, _pos):
        if x == 0:
            return '0'
        return f'{x:.1f}{unit}'
    ax.yaxis.set_major_formatter(plt.FuncFormatter(value_formatter))
    # Add grid and finalise
    ax.grid(axis='y', linestyle='--', alpha=0.3, color=grid_color)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def generate_free_cash_flow_chart(ticker, years=4, dark_theme=True):
    """Generate a chart showing free cash flow trend over time with improved text layout."""
    try:
        # FMP API
        financial_data, company_name = get_fmp_cashflow_data(ticker, years)
        if financial_data is None or len(financial_data) == 0:
            return None
        # Prepare chart data
        year_labels, fcf_scaled, _divisor, unit = prepare_fcf_data(
            financial_data)
        # Calculate CAGR for title
        cagr = calculate_cagr(fcf_scaled)
        # Setup chart theme
        bar_color, line_color, text_color, grid_color = setup_fcf_chart_theme(
            dark_theme)
        # Create figure and axes
        fig, ax = plt.subplots(figsize=(10, 6))
        plt.subplots_adjust(left=0.1, right=0.9, top=0.88, bottom=0.12)
        # Bar positions
        x = np.arange(len(year_labels))
        # Create bars and trend line
        _fcf_bars, _ax2 = create_fcf_bars_and_line(
            ax, x, fcf_scaled, bar_color, line_color)
        # Add growth rate annotations
        add_growth_annotations(ax, x, fcf_scaled)
        # Set title with CAGR included if available
        if cagr != 0:
            chart_title = f'{company_name}: Free Cash Flow Trend (CAGR: {
                cagr:.1f}%)'
        else:
            chart_title = f'{company_name}: Free Cash Flow Trend'
        ax.set_title(
            chart_title,
            fontsize=22,
            pad=15,
            color=text_color,
            fontweight='bold')
        # Add legend
        legend_elements = [
            Line2D([0], [0], color='none', marker='s', markersize=15,
                   markerfacecolor=bar_color, label="Free Cash Flow")
        ]
        _legend = ax.legend(handles=legend_elements, loc='upper left',
                           frameon=False, fontsize=14)

        # Configure axes
        configure_fcf_axes(ax, x, year_labels, unit, grid_color)
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
