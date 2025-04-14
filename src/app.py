import os
import json
import logging
import traceback
import contextlib
import io
import sys
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yfinance as yf
import psycopg2
from flask import Flask, request, jsonify, session, send_from_directory, Response
from werkzeug.security import generate_password_hash, check_password_hash
from prices import get_indicators
from esg import get_esg_indicators
from strategy import get_advice
from fundamentals import get_valuation


app = Flask(__name__, static_folder='../frontend/dist')
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
        # print(traceback.format_exc())
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
    session.pop('user_id', None) # Clearing user session
    logging.info("Logged out successfully")
    return jsonify({"message": "Logged out successfully."})

# dev get indicator crypto
@app.route('/indicators_crypto')
def indicators_crypto():
    # crypto tickers, can either be singular or a comma seperated list
    # e.g. BTC/USD or BTC/USD,ETH/USD,DOGE/USD
    arg1 = request.args.get('tickers', type = str)

    # indicaor names, as according to the TA-lib api, can either be
    # singular or a comma seperated list
    # e.g. SMA,EMA,BOOLBANDS
    arg2 = request.args.get('indicators', type = str)

    # time period in days
    # e.g. 30
    arg3 = request.args.get('time_period', type = int, default = '5')

    # resolution of the data, minute aggregates, hour aggregrates or
    # day aggregrates
    # e.g. min or hour or day
    arg4 = request.args.get('resolution', type = str, default = 'min')

    try:
        if arg1:
            tickers = list(map(str, arg1.split(',')))
        else:
            return jsonify({"message": "missing arg1, tickers (e.g: BTC/USD or BTC/USD,ETH/USD)"})
        if arg2:
            indicators = list(map(str, arg2.split(',')))
        else:
            return jsonify({"message": "missing arg2, indicators (e.g: SMA)"})
        if arg3:
            period = int(arg3)
        if arg4:
            resolution = str(arg4)

    except Exception as e:
        logging.error(f"Error invalid input parameters: %s", e)
        return jsonify({"message": "invalid inputs."}, 400)

    try:
        res = get_indicators(tickers, indicators, period, resolution)
        res = json.dumps(res, default=str)
        logging.info("Calculating Indicators")
        return jsonify(res)
    except Exception as _:
        logging.error(f"Error calculating indicators: %s", e)
        return jsonify({"message": "something went wrong while getting indicators."}, 400)

# dev get indicator stocks
@app.route('/indicators_stocks')
def indicators_stock():
    # Crypto is also supported but do not mix and match crypto tickers
    # together with stock tickers
    # e.g. AAPL,BTC/USD NOT ALLOWED
    # e.g. BTC/USD,ETH/USD OK

    # stock tickers, can either be singular or a comma seperated list
    # e.g. AAPL or AAPL,MSFT,NVDA,GOOG,AMZN
    arg1 = request.args.get('tickers', type = str)

    # indicaor names, as according to the TA-lib api, can either be
    # singular or a comma seperated list
    # e.g. SMA,EMA,BOOLBANDS
    arg2 = request.args.get('indicators', type = str)

    # time period in days
    # e.g. 30
    arg3 = request.args.get('time_period', type = int, default = '5')

    # resolution of the data, minute aggregates, hour aggregrates or
    # day aggregrates
    # e.g. min or hour or day
    arg4 = request.args.get('resolution', type = str, default = 'min')

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

    except Exception as e:

        logging.error(f"Error invalid input parameters: %s", e)
        return jsonify({"message": "invalid inputs."}, 400)

    try:
        res = get_indicators(tickers, indicators, period, resolution)
        res = json.dumps(res, default=str)
        logging.info("Calculating Indicators")
        return jsonify(res)
    except Exception as _:
        logging.error(f"Error calculating indicators: %s", e)
        return jsonify({"message": "something went wrong while getting indicators."}, 400)

# get esg indicators
@app.route('/indicators_esg')
def indicators_esg():
    try:
        # stock tickers, can either be singular or a comma seperated list
        # e.g. AAPL or AAPL,MSFT,NVDA,GOOG,AMZN
        arg1 = request.args.get('tickers', type = str)

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
        return jsonify({"message": "something went wrong while getting ESG data."}, 400)

# get advice
@app.route("/advice_v1")
def advice():
    res = get_advice()
    res = json.dumps(res, default=str)

    logging.info("Get Advice Sucess")
    return jsonify(res)


# fundamnetal analysis : pe, peg, ps, ebitda, price to free cash flow, free cash flow etc
@app.route("/fundamentals/valuation")
def fundamentals_valuation():
    ticker = request.args.get('ticker', type=str)

    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400
    try:
        # handles outputs for essential metrics (pe ps ebitda ... etc) + in dustry average for pe
        # will try to add industry average for other ratios but fmp does not include.
        # but industry average for pe is done so far. can start on that first.
        result = get_valuation(ticker)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# External Team's API
@app.route('/v1/retrieve/market-graph', methods=['GET'])
def get_market_graph():
    company_names = request.args.get('company_name')
    start_date = request.args.get('start_date')

    if not company_names or not start_date:
        logging.error("Missing required parameters for market graph")
        return jsonify({"error": "Missing required parameters"}), 400
        
    tickers = [ticker.strip() for ticker in company_names.split(',') if ticker.strip()]
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
                    return jsonify({"error": f"(x) download data for {t}: {download_err}"}), 500


            if data is None or data.empty:
                return jsonify({"error": f"No data found for {company_names}"}), 404
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

if __name__ == '__main__':
    logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

    logging.info("Application started")
    app.run(host='0.0.0.0', port=5000, debug=True)
