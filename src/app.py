import os
import json
import logging
import traceback
import psycopg2
from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from prices import get_indicators
from esg import get_esg_indicators
from strategy import get_advice

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
        logging.info("User registered successfully")
        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        # print(traceback.format_exc())
        logging.error(f"Registration error: %s", e)
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

# fundamnetal analysis : pe, peg, pb, ps, ebitda, price to free cash flow, graham number, enterprise value, earnings yield, free cash flow 
@app.route("/fundamentals/valuation")
def fundamentals_valuation():
    ticker = request.args.get('ticker', type=str)

    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400
    
    try:
        result = get_valuation(ticker)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500




if __name__ == '__main__':
    logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

    logging.info("Application started")
    app.run(host='0.0.0.0', port=5000, debug=True)
