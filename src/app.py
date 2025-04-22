import base64
import contextlib
from datetime import datetime
import io
import os
import json
import logging
import traceback
import numpy as np
import math
import matplotlib
import matplotlib.pyplot as plt
import psycopg2
import yfinance as yf
from flask import Flask, request, jsonify, session, send_from_directory, Response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from prices import get_indicators, get_prices
from esg import get_esg_indicators
from dcf_valuation import (
    calculate_dcf_valuation,
    generate_enhanced_valuation_chart,
    FAIR_VALUE_DATA,
    get_current_price
)
from fundamentals import (
    get_key_metrics_summary,
    generate_pe_plotly_endpoint,
    warm_sector_pe_cache
)
from fundamentals_historical import generate_yearly_performance_chart, generate_free_cash_flow_chart
from strategy import get_not_advice, get_not_advice_v2
from profiles import InvestmentGoal, RiskTolerance
from parallel_viz import generate_parallel_chart
from company_data import SECTORS
from data_layer.database import get_sqlite_connection 
from data_layer.data_access import get_selectable_companies, get_metrics_for_comparison
from formatter import format_comparison_data_for_plotly
from profiles import InvestmentGoal, RiskTolerance

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend/dist')
warm_sector_pe_cache() 
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'your_secret_key'
#
db_config = {
    'dbname': 'postgres',
    'user': 'foxtrot',
    'password': 'FiveGuys',
    'host': 'foxtrot-db.cialrzbfckl9.us-east-1.rds.amazonaws.com',
    'port': 5432
}


def get_db_connection():
    conn = psycopg2.connect(**db_config)
    return conn

# @app.route('/')
# def home():
#     return "Hello, Flask!"


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')
# Register


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username/Password required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM users WHERE username = %s;", [username])
        if cur.fetchone():
            return jsonify({'error': 'Username already exists'}), 400

        hashed_password = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s);",
            (username, hashed_password)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
        conn.close()

# Login


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        logging.info("Loggin not successful")
        return jsonify({'message': 'User logging not successful'}), 400
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM users WHERE username = %s;", [username])
        user = cur.fetchone()

        if not user or not check_password_hash(user[2], password):
            return jsonify({'error': 'Invalid username or password'}), 401

        session['user_id'] = user[0]
        logging.info("Logged in successfully")
        return jsonify({
            'message': f"User '{username}' logged in successfully.",
            'token': user[0]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
        conn.close()

# Logout


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  # Clearing user session
    logging.info("Logged out successfully")
    return jsonify({"message": "Logged out successfully."})

# dev get indicator crypto


@app.route('/indicators_crypto')
def indicators_crypto():
    # crypto tickers, can either be singular or a comma seperated list
    # e.g. BTC/USD or BTC/USD,ETH/USD,DOGE/USD
    arg1 = request.args.get('tickers', type=str)

    # indicaor names, as according to the TA-lib api, can either be
    # singular or a comma seperated list
    # e.g. SMA,EMA,BOOLBANDS
    arg2 = request.args.get('indicators', type=str)

    # time period in days
    # e.g. 30
    arg3 = request.args.get('time_period', type=int, default='5')

    # resolution of the data, minute aggregates, hour aggregrates or
    # day aggregrates
    # e.g. min or hour or day
    arg4 = request.args.get('resolution', type=str, default='min')
    # Optional: aggregate number of the data
    # e.g. if you want a 5 minute interval you would type '5' here.
    arg5 = request.args.get('agg', type=int, default='1')
    try:
        if arg1:
            tickers = list(map(str, arg1.split(',')))
        else:
            return jsonify(
                {"message": "missing arg1, tickers (e.g: BTC/USD or BTC/USD,ETH/USD)"})
        if arg2:
            indicators = list(map(str, arg2.split(',')))
        else:
            return jsonify({"message": "missing arg2, indicators (e.g: SMA)"})
        if arg3:
            period = int(arg3)
        if arg4:
            resolution = str(arg4)
        if arg5:
            agg = int(arg5)
    except Exception as e:
        logging.error(f"Error invalid input parameters: %s", e)
        return jsonify({"message": "invalid inputs."}, 400)

    try:
        res = get_indicators(
            tickers,
            indicators,
            period,
            resolution,
            agg_number=agg)
        res = json.dumps(res, default=str)
        logging.info("Calculating Indicators")
        return jsonify(res)
    except Exception as _:
        logging.error(f"Error calculating indicators: %s", e)
        return jsonify(
            {"message": "something went wrong while getting indicators."}, 400)

# dev get indicator stocks


@app.route('/indicators_stocks')
def indicators_stock():
    # Crypto is also supported but do not mix and match crypto tickers
    # together with stock tickers
    # e.g. AAPL,BTC/USD NOT ALLOWED
    # e.g. BTC/USD,ETH/USD OK

    # stock tickers, can either be singular or a comma seperated list
    # e.g. AAPL or AAPL,MSFT,NVDA,GOOG,AMZN
    arg1 = request.args.get('tickers', type=str)

    # indicaor names, as according to the TA-lib api, can either be
    # singular or a comma seperated list
    # e.g. SMA,EMA,BOOLBANDS
    arg2 = request.args.get('indicators', type=str)

    # time period in days
    # e.g. 30
    arg3 = request.args.get('time_period', type=int, default='5')

    # resolution of the data, minute aggregates, hour aggregrates or
    # day aggregrates
    # e.g. min or hour or day
    arg4 = request.args.get('resolution', type=str, default='min')

    # Optional: aggregate number of the data
    # e.g. if you want a 5 minute interval you would type '5' here.
    arg5 = request.args.get('agg', type=int, default='1')

    try:
        if arg1:
            tickers = list(map(str, arg1.split(',')))
        else:
            return jsonify({"message": "missing arg1, tickers (e.g: AAPL)"})
        if arg2:
            indicators = list(map(str, arg2.split(',')))
        else:
            return jsonify({"message": "missing arg2, indicators (e.g: SMA)"})
        if arg3:
            period = int(arg3)
        if arg4:
            resolution = str(arg4)
        if arg5:
            agg = int(arg5)
    except Exception as e:

        logging.error(f"Error invalid input parameters: %s", e)
        return jsonify({"message": "invalid inputs."}, 400)

    try:
        res = get_indicators(
            tickers,
            indicators,
            period,
            resolution,
            agg_number=agg)
        res = json.dumps(res, default=str)
        logging.info("Calculating Indicators")
        return jsonify(res)
    except Exception as _:
        logging.error(f"Error calculating indicators: %s", e)
        return jsonify(
            {"message": "something went wrong while getting indicators."}, 400)

# get esg indicators


@app.route('/indicators_esg')
def indicators_esg():
    try:
        # stock tickers, can either be singular or a comma seperated list
        # e.g. AAPL or AAPL,MSFT,NVDA,GOOG,AMZN
        arg1 = request.args.get('tickers', type=str)
        if arg1:
            tickers = list(map(str, arg1.split(',')))
        else:
            return jsonify({"message": "missing arg1, tickers (e.g: AAPL)"})

        res = get_esg_indicators(tickers)
        res = json.dumps(res, default=str)
        logging.info("Getting ESG data")
        return jsonify(res)
    except Exception as e:
        logging.error(f"Error getting esg indicators: %s", e)
        return jsonify(
            {"message": "something went wrong while getting ESG data."}, 400)

# get prices without indicators


@app.route("/get_prices")
def fetch_prices():
    # stock tickers, can either be singular or a comma seperated list
    # e.g. AAPL or AAPL,MSFT,NVDA,GOOG,AMZN
    # crypto tickers work too,
    # e.g. ETH/USD or BTC/USD,ETH/USD,DOGE/USD
    # keep in mind not to mix crypto tickers with stock tickers
    arg1 = request.args.get('tickers', type=str)
    # resolution, type String: min hour day
    arg2 = request.args.get('resolution', type=str, default='hour')
    # starting date in iso format 'YYYY-MM-DD'
    arg3 = request.args.get('start_date', type=str, default='2025-01-5')
    # ending date in iso format 'YYYY-MM-DD'
    arg4 = request.args.get('end_date', type=str, default='2025-01-20')
    if arg1:
        tickers = list(map(str, arg1.split(',')))
    else:
        return jsonify({"message": "missing arg1, tickers (e.g: AAPL)"})
    res = get_prices(tickers, arg2, start_date=arg3, end_date=arg4)
    logging.info("Get prices success")
    return jsonify(res)

# get analysis


@app.route("/get_analysis_v1")
def analysis_v1():
    res = get_not_advice()
    res = json.dumps(res, default=str)

    logging.info("Get analysis success")
    return jsonify(res)

# get analysis version 2


@app.route("/get_analysis_v2")
def analysis_v2():
    try:
        # stock tickers, can either be singular or a comma seperated list
        # e.g. AAPL or AAPL,MSFT,NVDA,GOOG,AMZN
        # crypto tickers work too,
        # e.g. ETH/USD or BTC/USD,ETH/USD,DOGE/USD
        # keep in mind not to mix crypto tickers with stock tickers
        arg1 = request.args.get('tickers', type=str)
        # time at which the data updates, minutely hourly or daily
        # note that minutely updates only support crypto at the moment
        arg2 = request.args.get('resolution', type=str, default='hour')

        if arg1:
            tickers = list(map(str, arg1.split(',')))
        else:
            return jsonify({"message": "missing arg1, tickers (e.g: AAPL)"})
        if arg2:
            resolution = str(arg2)
    except Exception as e:
        logging.error(f"Error invalid input parameters: %s", e)
        return jsonify({"message": "invalid inputs."}, 400)

    res = get_not_advice_v2(tickers, resolution)
    logging.info("Get Analysis Sucess")
    return jsonify(res)


@app.route("/fundamentals/key_metrics")
def fundamentals_valuation():
    ticker = request.args.get('ticker', type=str)
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400
    try:
        # handles outputs for essential metrics
        result = get_key_metrics_summary(ticker)
        print(f"INFO: Returning result for {ticker}: {json.dumps(result)}")
        return jsonify(result)
    except Exception as e:
        print(f"ERROR: Exception in fundamentals_valuation: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/sectors', methods=['GET'])
def api_get_sectors():
    """Returns the list of available sectors keys."""
    try:
        sector_list = list(SECTORS.keys())
        return jsonify(sorted(sector_list))
    except Exception as e:
        logging.exception("Error fetching sectors")
        return jsonify({"error": "Could not retrieve sectors"}), 500

@app.route('/api/selectable_companies', methods=['GET'])
def api_get_selectable_companies():
    """Returns a list of companies available in the cache."""
    try:
        companies = get_selectable_companies() 
        return jsonify(companies)
    except Exception as e:
        logging.exception("Error fetching selectable companies")
        return jsonify({"error": "Could not retrieve company list"}), 500


@app.route('/api/compare', methods=['GET'])
def api_compare_companies_cached():
    """Provides data needed for the frontend parallel coordinates chart."""
    tickers_str = request.args.get('tickers') 
    if not tickers_str: return jsonify({"error": "Ticker symbols are required"}), 400

    ticker_list = [t.strip().upper() for t in tickers_str.split(',') if t.strip()]
    if not ticker_list or len(ticker_list) > 15: return jsonify({"error": "Invalid/too many tickers"}), 400

    try:
        # 1. Fetch stored metrics for the selected tickers from SQLite Cache
        comparison_metrics = get_metrics_for_comparison(ticker_list) # from data_access.py
        if not comparison_metrics: return jsonify({"error": "No data for tickers"}), 404

        # 2. Format data into the structure needed by Plotly.js
        plotly_data = format_comparison_data_for_plotly(comparison_metrics) 

        return jsonify(plotly_data) 

    except Exception as e:
        logging.exception("Error in /api/compare endpoint")
        return jsonify({"error": "Failed to generate comparison data"}), 500



@app.route("/fundamentals/pe_chart")
def pe_ratio_chart():
    ticker = request.args.get('ticker', type=str)
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400

    try:
        # Get theme parameter (defaulting to dark)
        dark_theme = request.args.get('theme', 'dark').lower() == 'dark'
        theme = 'dark' if dark_theme else 'light'
        print(f"INFO: Using {theme} theme for PE chart")

        # Get chart type (matplotlib or plotly)
        chart_type = request.args.get('type', 'plotly').lower()

        # Get response format
        response_format = request.args.get('format', 'json').lower()
        print(f"INFO: Requested response format: {response_format}")
        if response_format not in ['json', 'png']:
            return jsonify(
                {'error': 'Format must be either "json" or "png"'}), 400

        # Fetch metrics data
        metrics = get_key_metrics_summary(ticker)
        if not metrics:
            return jsonify({"error": "Could not retrieve metrics data"}), 500

        # Extract PE values
        pe_ratio = metrics.get("pe", 0)
        sector_pe = metrics.get("sector_pe", 0)

        # Special handling for None or NaN values
        if pe_ratio is None or np.isnan(pe_ratio):
            pe_ratio = 0
        if sector_pe is None or np.isnan(sector_pe):
            sector_pe = 0
        print(
            f"INFO: Generating PE chart for {ticker} "
            f"(PE: {pe_ratio}, Sector PE: {sector_pe})"
        )
        # Generate the gauge chart based on requested type
        if chart_type == 'plotly':
            img_str = generate_pe_plotly_endpoint(
                ticker, pe_ratio, sector_pe, dark_theme)
            if not img_str:
                return jsonify(
                    {"error": "Failed to generate plotly PE chart"}), 500
        else:
            # Default to matplotlib if not plotly
            # Assuming a default implementation if plotly fails
            return jsonify(
                {"error": "Matplotlib chart generation not implemented"}), 501

        # Return based on requested format
        if response_format == 'json':
            print("INFO: Returning JSON response with PE chart")
            return jsonify({
                'ticker': ticker,
                'pe_ratio': pe_ratio,
                'sector_pe': sector_pe,
                'chart': img_str,
                'chart_type': chart_type
            })

        # Return PNG image directly
        try:
            print("INFO: Creating PNG response")
            img_data = base64.b64decode(img_str)
            response = Response(
                img_data,
                mimetype='image/png',
                headers={
                    'Content-Disposition': f'inline; filename={ticker}_pe_chart.png',
                    'Cache-Control': 'no-cache'})
            return response
        except Exception as e:
            return jsonify({'error': f'Failed to generate PNG: {str(e)}'}), 500

    except Exception as e:
        print(f"ERROR: Exception in pe_ratio_chart: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/fundamentals/calculate_dcf', methods=['GET'])
def calculate_dcf_endpoint():
    """Calculate DCF valuation for a ticker using manual calculation"""
    ticker = request.args.get('ticker', '')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    # Calculate DCF valuation
    dcf_result = calculate_dcf_valuation(ticker)
    if not dcf_result:
        return jsonify(
            {'error': f'Failed to calculate DCF valuation for {ticker}'}), 500

    # Return JSON response with detailed calculation
    return jsonify({
        'ticker': dcf_result['ticker'],
        'company_name': dcf_result['company_name'],
        'current_price': dcf_result['current_price'],
        'fair_value': dcf_result['fair_value'],
        'potential': dcf_result['potential'],
        'valuation_status': dcf_result['valuation_status'],
        'market_cap': dcf_result['market_cap'],
        'discount_rate': dcf_result['wacc'],
        'growth_rate': dcf_result['historical_growth_rate'],
        'terminal_growth_rate': dcf_result['terminal_growth_rate'],
        'calculation_date': dcf_result['calculation_date']
    })


@app.route('/fundamentals/enhanced_valuation_chart', methods=['GET'])
def enhanced_valuation_chart():
    """Generate an enhanced intrinsic value chart with bright colors and company logo"""
    ticker = request.args.get('ticker', '')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    # Get theme parameter (defaulting to dark)
    dark_theme = request.args.get('theme', 'dark').lower() == 'dark'
    response_format = request.args.get('format', 'png').lower()

    # Generate the chart
    img_str = generate_enhanced_valuation_chart(ticker, dark_theme)
    if not img_str:
        return jsonify({'error': 'Failed to generate valuation chart'}), 500

    # Get current price and company name for response
    current_price, company_name = get_current_price(ticker)

    # Get fair value and calculate valuation percentage
    ticker = ticker.upper()
    if ticker in FAIR_VALUE_DATA:
        fair_value = FAIR_VALUE_DATA[ticker]["fair_value"]
        if current_price > 0 and fair_value > 0:
            potential = ((fair_value / current_price) - 1) * 100
            valuation_status = "Undervalued" if potential >= 0 else "Overvalued"
        else:
            potential = 0
            valuation_status = "Unknown"
    else:
        fair_value = 0
        potential = 0
        valuation_status = "Unknown"

    # Return response based on requested format
    if response_format == 'json':
        return jsonify({
            'ticker': ticker,
            'company_name': company_name,
            'current_price': current_price,
            'fair_value': fair_value,
            'potential': potential,
            'valuation_status': valuation_status,
            'chart': img_str
        })
    try:
        img_data = base64.b64decode(img_str)
        response = Response(img_data, mimetype='image/png')
        response.headers['Content-Disposition'] = f'inline; filename={
            ticker}_valuation.png'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception as e:
        return jsonify({'error': f'Failed to generate PNG: {str(e)}'}), 500




# historical graphs for the earnings
@app.route('/fundamentals_historical/generate_yearly_performance_chart',
           methods=['GET'])
def quarterly_performance_endpoint():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker parameter is required'}), 400

    try:
        quarters = int(request.args.get('quarters', '4'))
        if quarters < 1 or quarters > 12:
            return jsonify({'error': 'Quarters must be between 1 and 12'}), 400
    except ValueError:
        return jsonify({'error': 'Quarters must be a valid integer'}), 400

    dark_theme = request.args.get('dark_theme', 'true').lower() == 'true'
    response_format = request.args.get('format', 'json')

    if response_format not in ['json', 'png']:
        return jsonify({'error': 'Format must be either "json" or "png"'}), 400

    # Generate the chart
    img_str = generate_yearly_performance_chart(ticker, quarters, dark_theme)

    if not img_str:
        return jsonify({'error': 'Failed to generate chart'}), 500

    # Return based on requested format
    if response_format == 'json':
        return jsonify({
            'ticker': ticker,
            'chart': img_str
        })
    try:
        print("INFO: Decoding base64 data for PNG response")
        img_data = base64.b64decode(img_str)
        print("INFO: Creating PNG response")
        response = Response(
            img_data,
            mimetype='image/png',
            headers={
                'Content-Disposition': f'inline; filename={ticker}_free_cash_flow.png',
                'Cache-Control': 'no-cache'})
        return response
    except Exception as e:
        return jsonify({'error': f'Failed to generate PNG: {str(e)}'}), 500


@app.route('/fundamentals_historical/free_cash_flow_chart', methods=['GET'])
def free_cash_flow_endpoint():
    """Generate a chart showing free cash flow trend using FMP data."""
    ticker = request.args.get('ticker')
    if not ticker:
        print("ERROR: Missing ticker parameter")
        return jsonify({'error': 'Ticker parameter is required'}), 400

    try:
        years = int(request.args.get('years', '4'))
        if years < 1 or years > 12:
            print(f"ERROR: Invalid years parameter: {years}")
            return jsonify({'error': 'Years must be between 1 and 12'}), 400
    except ValueError:
        print(
            f"ERROR: Non-integer years parameter: {request.args.get('years')}")
        return jsonify({'error': 'Years must be a valid integer'}), 400

    # Get theme parameter (defaulting to dark)
    dark_theme = request.args.get('theme', 'dark').lower() == 'dark'
    print(f"INFO: Using {'dark' if dark_theme else 'light'} theme for chart")

    # Get response format
    response_format = request.args.get('format', 'json').lower()
    print(f"INFO: Requested response format: {response_format}")

    if response_format not in ['json', 'png']:
        return jsonify({'error': 'Format must be either "json" or "png"'}), 400

    # Generate the chart
    print(f"INFO: Calling generate_free_cash_flow_chart for {ticker}")
    img_str = generate_free_cash_flow_chart(ticker, years, dark_theme)

    if not img_str:
        return jsonify({'error': 'Failed to generate chart'}), 500

    print(f"INFO: Chart generated successfully, data length: {len(img_str)}")

    # Return based on requested format
    if response_format == 'json':
        print("INFO: Returning JSON response")
        return jsonify({
            'ticker': ticker,
            'chart': img_str
        })

    try:
        print("INFO: Decoding base64 data for PNG response")
        img_data = base64.b64decode(img_str)

        print("INFO: Creating PNG response")
        response = Response(
            img_data,
            mimetype='image/png',
            headers={
                'Content-Disposition': f'inline; filename={ticker}_free_cash_flow.png',
                'Cache-Control': 'no-cache'})
        return response
    except Exception as e:
        return jsonify({'error': f'Failed to generate PNG: {str(e)}'}), 500


# External Team's API
@app.route('/v1/retrieve/market-graph', methods=['GET'])
def get_market_graph():
    company_names = request.args.get('company_name')
    start_date = request.args.get('start_date')

    if not company_names or not start_date:
        logging.error("Missing required parameters for market graph")
        return jsonify({"error": "Missing required parameters"}), 400

    tickers = [ticker.strip()
               for ticker in company_names.split(',') if ticker.strip()]
    try:
        fig = plt.figure(figsize=(12, 8))
        for t in tickers:
            f = io.StringIO()
            data = None
            with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
                try:
                    # Get market data using yfinance
                    data = yf.download(t, start=start_date)
                except Exception as download_err:
                    # Log the actual download error if it happens
                    return jsonify(
                        {"error": f"(x) download data for {t}: {download_err}"}), 500

            if data is None or data.empty:
                return jsonify(
                    {"error": f"No data found for {company_names}"}), 404
            # Create the graph
            fig = plt.figure(figsize=(10, 6))
            plt.plot(data['Close'], label='Close Price')
            plt.plot(data['High'], label='High Price')
            plt.plot(data['Low'], label='Low Price')
            plt.plot(data['Open'], label='Open Price')

            plt.title(f'{company_names} Stock Price')
            plt.xlabel('Date')
            plt.ylabel('Price (USD)')
            plt.grid(True)
            plt.legend()
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            plt.close(fig)
            buffer.seek(0)
            # Send the image as response using Response
            return Response(buffer.getvalue(), mimetype='image/png')
    except Exception as e:
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500


# pylint: disable=pointless-string-statement
"""
@app.route('/api/v1/graph/<from_currency>/<to_currency>/last-week', methods=['GET'])
def exchange_rate_graph(from_currency, to_currency):
    try:
        # Fetch raw PNG bytes from the mock server
        png_data = fetch_exchange_rate_graph(from_currency, to_currency)
        return Response(png_data, mimetype='image/png')
    except Exception as e:
        # If there's an error or the server returns a non-200 status,
        # respond with an error message in JSON
        return jsonify({"error": str(e)}), 500



@app.route('/reports/')
def serve_report(filename):
    # Serve generated report files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, 'reports')
    file_path = os.path.join(reports_dir, filename)

    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({"error": f"File not found: {filename}"}), 404
"""

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    logging.info("Application started")
    app.run(host='0.0.0.0', port=5000, debug=True)
