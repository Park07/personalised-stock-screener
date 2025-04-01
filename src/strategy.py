import threading
import json
from datetime import datetime, timezone
import asyncio
import logging # Import logging
import numpy as np
import talib
import talib.abstract
import websockets
from .config import ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY
import sys # Import sys for exiting if keys are missing

# --- Basic Logging Configuration ---
# Configure logging - This is important to see the output
# You might want to adjust the level (e.g., logging.DEBUG for more detail)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s'
)
# ---------------------------------

# --- Check if API Keys are loaded from config ---
logging.info(f"Loaded ALPACA_PUBLIC_KEY: {ALPACA_PUBLIC_KEY}")
# Mask the secret key when logging it for security
logging.info(f"Loaded ALPACA_SECRET_KEY: {'******' if ALPACA_SECRET_KEY else 'None'}")

# CRITICAL CHECK: Exit if keys are not loaded from environment
if not ALPACA_PUBLIC_KEY or not ALPACA_SECRET_KEY:
    logging.error("--------------------------------------------------------------------")
    logging.error("CRITICAL: Alpaca API keys not found or not loaded from environment!")
    logging.error("Please ensure ALPACA_PUBLIC_KEY and ALPACA_SECRET_KEY are exported")
    logging.error("in the SAME terminal session before running the script.")
    logging.error("Exiting script.")
    logging.error("--------------------------------------------------------------------")
    sys.exit("Exiting: Alpaca API keys not loaded.") # Stop execution
else:
    logging.info("Alpaca keys seem loaded into Python from config.")
# -------------------------------------------------


# due to limitations on a free alpaca plan
# we can only work with live data on 30 tickers
# supported_companies = ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'BRK.B',
#                        'AVGO', 'TSLA', 'JPM', 'LLY', 'V', 'XOM', 'UNH', 'MA',
#                        'NFLX', 'COST', 'PG', 'WMT', 'HD', 'ABBV', 'CVX', 'CRM',
#                        'KO', 'ORCL', 'WFC', 'CSCO', 'PM']
supported_currencies = ["BTC/USD", 'DOGE/USD', 'ETH/USD', 'LINK/USD', 'LTC/USD',
                        'SUSHI/USD', 'UNI/USD', 'YFI/USD']
# --- Consider simplifying for testing ---
# supported_currencies = ["BTC/USD"]
# logging.warning(f"Using simplified currency list for testing: {supported_currencies}")
# -----------------------------------------


def SMA_MOMENTUM_strategy(data):
    sma = talib.abstract.SMA
    # moving avg momentum strat
    if data is None or 'open' not in data or len(data['open']) <= 20:
         logging.debug("SMA_MOMENTUM: Insufficient data, returning HOLD")
         return 'HOLD'
    try:
        sma10 = sma(data, timeperiod=10)
        sma20 = sma(data, timeperiod=20)

        if sma10[-1] > sma20[-1]:
            logging.debug(f"SMA_MOMENTUM: Signal BUY (SMA10={sma10[-1]:.2f} > SMA20={sma20[-1]:.2f})")
            return 'BUY'
        if sma10[-1] < sma20[-1]:
            logging.debug(f"SMA_MOMENTUM: Signal SELL (SMA10={sma10[-1]:.2f} < SMA20={sma20[-1]:.2f})")
            return 'SELL'
    except Exception as e:
        logging.error(f"Error in SMA_MOMENTUM strategy: {e}")
    logging.debug("SMA_MOMENTUM: No signal, returning HOLD")
    return 'HOLD'

def BBANDS_strategy(data):
    bbands = talib.abstract.BBANDS

    if data is None or 'close' not in data or len(data['close']) < 20:
        logging.debug("BBANDS: Insufficient data, returning HOLD")
        return "HOLD"
    try:
        upper, _, lower = bbands(data, timeperiod=20)
        if data['close'][-1] > upper[-1]:
            logging.debug(f"BBANDS: Signal SELL (Close={data['close'][-1]:.2f} > Upper={upper[-1]:.2f})")
            return "SELL"
        if data['close'][-1] < lower[-1]:
            logging.debug(f"BBANDS: Signal BUY (Close={data['close'][-1]:.2f} < Lower={lower[-1]:.2f})")
            return "BUY"
    except Exception as e:
        logging.error(f"Error in BBANDS strategy: {e}")
    logging.debug("BBANDS: No signal, returning HOLD")
    return "HOLD"

def EMA_strategy(data):
    ema = talib.abstract.EMA
    if data is None or 'close' not in data or len(data['close']) < 30: # EMA uses timeperiod=30
        logging.debug("EMA: Insufficient data, returning HOLD")
        return "HOLD"
    try:
        ema_res = ema(data['close'], timeperiod=30)
        if data['close'][-1] > ema_res[-1] * 1.01:
            logging.debug(f"EMA: Signal BUY (Close={data['close'][-1]:.2f} > EMA={ema_res[-1]:.2f} * 1.01)")
            return "BUY"
        if data['close'][-1] < ema_res[-1] * 0.99:
            logging.debug(f"EMA: Signal SELL (Close={data['close'][-1]:.2f} < EMA={ema_res[-1]:.2f} * 0.99)")
            return "SELL"
    except Exception as e:
        logging.error(f"Error in EMA strategy: {e}")
    logging.debug("EMA: No signal, returning HOLD")
    return "HOLD"

def VWAP_strategy(data):
    """
    ( high + Low + Close ) / 3 - Simplified typical price used here
    VWAP = Sum(Typical Price * Volume) / Sum(Volume) over the period
    """
    if data is None or any(k not in data for k in ['high', 'low', 'close', 'volume']) or len(data['close']) < 1: # Need at least 1 bar
        logging.debug("VWAP: Insufficient data, returning HOLD")
        return "HOLD"
    try:
        # Ensure all arrays have the same length for calculation
        min_len = min(len(data['high']), len(data['low']), len(data['close']), len(data['volume']))
        if min_len == 0:
            logging.debug("VWAP: Data arrays are empty, returning HOLD")
            return "HOLD"

        high = data['high'][-min_len:]
        low = data['low'][-min_len:]
        close = data['close'][-min_len:]
        volume = data['volume'][-min_len:]

        typical_price = (high + low + close) / 3
        # Check for zero total volume to avoid division by zero
        total_volume = np.sum(volume)
        if total_volume == 0:
            logging.debug("VWAP: Total volume is zero, returning HOLD")
            return "HOLD"

        vwap = np.sum(typical_price * volume) / total_volume
        latest_close = close[-1]

        if latest_close > vwap * (1.03):
             logging.debug(f"VWAP: Signal BUY (Close={latest_close:.2f} > VWAP={vwap:.2f} * 1.03)")
             return "BUY"
        if latest_close < vwap * (0.97):
             logging.debug(f"VWAP: Signal SELL (Close={latest_close:.2f} < VWAP={vwap:.2f} * 0.97)")
             return "SELL"
    except Exception as e:
        logging.error(f"Error in VWAP strategy: {e}")
    logging.debug("VWAP: No signal, returning HOLD")
    return "HOLD"

# Additional example: CDL2CROWS strategy
def CDL2CROWS_strategy(data):
    if data is None or any(k not in data for k in ['open', 'high', 'low', 'close']) or len(data['close']) < 3:
        logging.debug("CDL2CROWS: Insufficient data, returning HOLD")
        return "HOLD"
    try:
        cdl2crows_vals = talib.CDL2CROWS(
            data['open'], data['high'], data['low'], data['close']
        )
        # CDL2CROWS returns 0 (no pattern), 100 (bullish?), -100 (bearish)
        # Check TA-Lib docs for exact meaning, usually > 0 is bullish, < 0 is bearish
        if cdl2crows_vals[-1] > 0:
             logging.debug(f"CDL2CROWS: Signal BUY (Value={cdl2crows_vals[-1]})")
             return "BUY"
        elif cdl2crows_vals[-1] < 0:
             logging.debug(f"CDL2CROWS: Signal SELL (Value={cdl2crows_vals[-1]})")
             return "SELL"
    except Exception as e:
        logging.error(f"Error in CDL2CROWS strategy: {e}")
    logging.debug("CDL2CROWS: No signal, returning HOLD")
    return "HOLD"

# ADD FUNCTION NAME HERE
strategies = [SMA_MOMENTUM_strategy, BBANDS_strategy, EMA_strategy, VWAP_strategy, CDL2CROWS_strategy] # Added CDL one

"""
calculate probabilites schema
{
    # instrument name
    instrument: ETH/USD
    BUY: 20%
    SELL: 50%
    HOLD: 30%
}
"""

def count_buy_sell_hold(return_dict_slice, x):
    if not return_dict_slice: # Handle empty list
        return 0
    count = 0
    for element in return_dict_slice:
        if element.get("advice") == x: # Use .get for safety
            count += 1
    return (count / len(return_dict_slice)) * 100

def calculate_probabilities():
    probabilities_dict = {}
    time_stamp = datetime.now(timezone.utc)
    # Use .items() for iterating dicts, and .get for safe access
    for currency, history in return_dict.items():
        if history: # Check if list is not empty
            last_minute_advices = history[-1]
            if last_minute_advices: # Check if inner list is not empty
                buy_percent = count_buy_sell_hold(last_minute_advices, "BUY")
                sell_percent = count_buy_sell_hold(last_minute_advices, "SELL")
                hold_percent = count_buy_sell_hold(last_minute_advices, "HOLD")
                tmp = {
                    "buy": buy_percent,
                    "sell": sell_percent,
                    "hold": hold_percent,
                    "time_stamp": time_stamp, # Use the same timestamp for all calcs in this run
                }
                probabilities_dict[currency] = tmp
            else:
                 logging.debug(f"No advices found for {currency} in the last minute.")
        else:
            logging.debug(f"No history found for {currency}.")

    logging.info(f"Calculated Probabilities: {probabilities_dict}")
    return probabilities_dict

"""
RETURN DICT SCHEMA
{
    # instrument name
    ETH/USD: [
        # each minute, there is a new array, calculated from the prices
        # comming in from the websocket
        [
            # Array of strategy outputs which
            # looks like the one below
            {
                timestamp: 2025-03-29T08:17:00
                strategy_name: SMA_strategy
                advice: HOLD
            }

        ]
    ]

}
"""
# This dictionary will store data across different threads if run with Flask,
# ensure thread safety if needed, but for standalone -m run, it's okay.
return_dict = {}

def get_advice():
    """Called by Flask app to get latest calculated probabilities."""
    logging.info("get_advice() called.")
    return calculate_probabilities()

# THIS FUNCTION IS NOT THREAD SAFE if multiple threads call it concurrently
# which shouldn't happen in the standalone script setup.
async def connect_to_websocket():
    # This dictionary holds bars received in the current connection attempt
    data_dict = {}

    # uri = "wss://stream.data.alpaca.markets/v2/iex" # Stocks IEX v2
    # uri = "wss://stream.data.alpaca.markets/v2/sip" # Stocks SIP v2 (might require paid plan)
    # --- Ensure you use the correct endpoint for your keys/plan ---
    uri = "wss://stream.data.alpaca.markets/v1beta3/crypto/us" # Crypto v1beta3
    # uri = "wss://paper-api.alpaca.markets/stream" # Example Paper Trading stream (check docs)
    # ------------------------------------------------------------
    logging.info(f"Attempting to connect to websocket URI: {uri}")

    # Add connection timeout (e.g., 10 seconds)
    try:
        async with websockets.connect(uri, ping_interval=20, ping_timeout=10, close_timeout=10) as websocket:
            logging.info(f"WebSocket connection established successfully to {uri}.")

            logging.info("Attempting authentication...")
            auth_data = {
                "action": "auth",
                "key": ALPACA_PUBLIC_KEY,
                "secret": ALPACA_SECRET_KEY
            }
            await websocket.send(json.dumps(auth_data))
            logging.info("Authentication message sent.")

            # Optional: Wait for auth confirmation (Alpaca might send a message)
            # try:
            #     auth_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            #     logging.info(f"Received message after auth attempt: {auth_response}")
            # except asyncio.TimeoutError:
            #     logging.warning("Did not receive message within 5s of sending auth.")

            logging.info(f"Attempting to subscribe to bars: {supported_currencies}")
            subscribe_data = {
                "action": "subscribe",
                "bars": supported_currencies
            }
            await websocket.send(json.dumps(subscribe_data))
            logging.info("Subscription message sent.")

            logging.info("Waiting indefinitely for messages...")
            async for message in websocket:
                try:
                    # Log raw message (or part of it) for debugging
                    logging.debug(f"Received raw message: {message[:200]}...") # Log first 200 chars

                    data = json.loads(message)

                    # Alpaca streams often send lists of objects
                    if isinstance(data, list) and len(data) > 0:
                        msg_obj = data[0] # Process the first object in the list
                        msg_type = msg_obj.get('T') # 'T' is often the message type indicator

                        if msg_type == 'error':
                            logging.error(f"Alpaca Server Error Message: {msg_obj.get('msg')} (Code: {msg_obj.get('code')})")
                            # Consider breaking or specific handling based on error code
                            if msg_obj.get('code') in [401, 402, 403, 404, 405, 406]: # Auth/Sub errors
                                logging.critical("Received critical auth/sub error. Breaking connection loop.")
                                raise websockets.exceptions.ConnectionClosed(rcvd=None, sent=None) # Force closure

                        elif msg_type == 'success':
                             logging.info(f"Alpaca Success Message: {msg_obj.get('msg')}")

                        elif msg_type == 'subscription':
                             logging.info(f"Subscription Update: Subscribed to {msg_obj.get('bars')}, Trades: {msg_obj.get('trades')}, Quotes: {msg_obj.get('quotes')}")

                        elif msg_type == 'b': # 'b' usually indicates a bar message for crypto
                            bar = msg_obj
                            instrument_name = bar.get('S') # Use .get for safety

                            if not instrument_name:
                                logging.warning(f"Received bar message without symbol: {bar}")
                                continue # Skip this message

                            # --- Bar Processing Logic ---
                            # Add bar to specific instrument's list
                            if instrument_name not in data_dict:
                                data_dict[instrument_name] = []
                            data_dict[instrument_name].append(bar)

                            # Limit stored bars per instrument (circular buffer)
                            if len(data_dict[instrument_name]) > 100: # Keep last 100 bars
                                data_dict[instrument_name].pop(0)
                            # --------------------------

                            # --- Strategy Calculation (maybe less frequent?) ---
                            # Consider if you need to run strategies on *every* bar message
                            # or perhaps aggregate/run periodically (e.g., every minute)
                            time_stamp = datetime.now(timezone.utc) # Timestamp for this calculation run
                            strat_output_array = []

                            # Only calculate for the instrument that just received a bar
                            if instrument_name in data_dict and len(data_dict[instrument_name]) > 1: # Need some data
                                talib_input_dict = prepare_inputs_live(data_dict[instrument_name])
                                if talib_input_dict: # Check if prepare_inputs was successful
                                    for strat in strategies:
                                        strat_output = strat(talib_input_dict)
                                        formatted_output = format_return_dict(
                                            time_stamp=time_stamp,
                                            strategy_name=strat.__name__,
                                            buy_sell_hold=strat_output,
                                        )
                                        strat_output_array.append(formatted_output)
                                else:
                                     logging.warning(f"Failed to prepare inputs for {instrument_name}")

                            # --- Store Results ---
                            if strat_output_array: # Only append if strategies ran
                                if instrument_name not in return_dict:
                                    return_dict[instrument_name] = []
                                # Append the list of strategy results for this update
                                return_dict[instrument_name].append(strat_output_array)
                                # Optional: Limit history length in return_dict as well
                                if len(return_dict[instrument_name]) > 200: # Keep last 200 mins of results
                                    return_dict[instrument_name].pop(0)
                            # -------------------
                        else:
                             logging.warning(f"Received unhandled message type '{msg_type}': {msg_obj}")

                    else:
                        logging.warning(f"Received non-list or empty list message: {data}")

                except json.JSONDecodeError:
                    logging.error(f"Failed to decode JSON from message: {message}")
                except Exception as e:
                    logging.error(f"Error processing received message: {e}", exc_info=True) # Log full traceback for unexpected errors

    # Add specific exception handling
    except websockets.exceptions.ConnectionClosedOK as e:
        logging.info(f"WebSocket Connection Closed OK: Code={e.code}, Reason='{e.reason}'")
    except websockets.exceptions.ConnectionClosedError as e:
        # This is the error you were seeing - log more details if available
        logging.error(f"WebSocket Connection Closed Error: Code={e.code}, Reason='{e.reason}'")
        # Re-raise to trigger the reconnect loop in run_websocket
        raise e
    except websockets.exceptions.InvalidURI as e:
        logging.error(f"Invalid WebSocket URI: {uri} - {e}")
        raise e # Stop if URI is fundamentally wrong
    except websockets.exceptions.WebSocketException as e:
        logging.error(f"General WebSocket exception during connection: {e}")
        raise e # Re-raise general WS errors
    except ConnectionRefusedError as e:
         logging.error(f"Connection Refused: Could not connect to {uri}. Check host/port/firewall. {e}")
         raise e # Re-raise
    except OSError as e:
        # Catch OS-level errors like Network is unreachable
        logging.error(f"OS Error during connection (Network issue?): {e}")
        raise e # Re-raise
    except Exception as e:
        # Catch any other unexpected error during connection setup/handling
        logging.error(f"Unexpected error in connect_to_websocket: {e}", exc_info=True)
        raise e # Re-raise


def format_return_dict(time_stamp, strategy_name, buy_sell_hold):
    new_element = {
        "time_stamp": time_stamp.isoformat(), # Convert datetime to ISO string for easier JSON later
        "strategy_name": str(strategy_name),
        "advice": str(buy_sell_hold),
    }
    return new_element

async def run_websocket():
    """Main loop to run the websocket connection and handle reconnects."""
    while True:
        try:
            logging.info("Calling connect_to_websocket...")
            await connect_to_websocket()
        except (websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK,
                websockets.exceptions.WebSocketException,
                ConnectionRefusedError,
                OSError) as e:
            # Catch specific expected disconnection/network errors
            logging.warning(f"WebSocket connection issue: {type(e).__name__} - {e}. Attempting reconnect in 5 seconds...")
        except Exception as e:
            # Catch other unexpected errors from connect_to_websocket
            logging.error(f"Unexpected error in run_websocket loop: {e}", exc_info=True)
            logging.warning("Attempting reconnect in 5 seconds...")

        # Wait before attempting to reconnect
        await asyncio.sleep(5)


def prepare_inputs_live(stock_bars):
    """
    Takes in a list of stock bars received from websocket.
    Formats them for inputting into the TA-Lib abstract functions.

    :param stock_bars: a list of bar dictionaries e.g. [{'o':..., 'h':..., 'l':..., 'c':..., 'v':..., 'S':..., 't':...}]
    :return: dict of ndarrays with keys {'open', 'high', 'low', 'close', 'volume'} or None on error
    """
    if not isinstance(stock_bars, list) or not stock_bars:
        logging.warning("prepare_inputs_live: Received empty or non-list input.")
        return None
    try:
        # Using lists first is often more efficient than repeated np.append
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []

        required_keys = ['o', 'h', 'l', 'c', 'v']
        for bar in stock_bars:
            if not isinstance(bar, dict):
                 logging.warning(f"Skipping non-dict item in stock_bars: {bar}")
                 continue
            if all(key in bar for key in required_keys):
                opens.append(bar['o'])
                highs.append(bar['h'])
                lows.append(bar['l'])
                closes.append(bar['c'])
                volumes.append(bar['v'])
            else:
                logging.warning(f"Skipping bar with missing keys: {bar}")

        # Check if any data was actually collected
        if not closes:
             logging.warning("prepare_inputs_live: No valid bars found to process.")
             return None

        # Convert to numpy arrays for TA-Lib
        # Specify dtype=float to handle potential variations and avoid issues
        return {
            'open': np.array(opens, dtype=float),
            'high': np.array(highs, dtype=float),
            'low': np.array(lows, dtype=float),
            'close': np.array(closes, dtype=float),
            'volume': np.array(volumes, dtype=float)
        }
    except Exception as e:
        # Log the error and the type/first few items of input for debugging
        logging.error(f"Error processing inputs for talib: {e} | Input type: {type(stock_bars)} | First item: {stock_bars[0] if stock_bars else 'N/A'}", exc_info=True)
        return None # Return None to indicate failure

def start_websocket_in_background():
    """Starts the asyncio websocket event loop in a separate thread."""
    logging.info("Starting WebSocket listener thread...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_websocket())
    except Exception as e:
        logging.critical(f"WebSocket background thread crashed: {e}", exc_info=True)
    finally:
        logging.info("WebSocket listener thread finished.")


# --- Main execution block for running standalone ---
if __name__ == "__main__":
    logging.info("Running strategy.py in standalone mode (__name__ == '__main__')")

    # Start the websocket connection in a background daemon thread
    # Daemon=True means the thread won't prevent the main script from exiting
    websocket_thread = threading.Thread(target=start_websocket_in_background, daemon=True)
    websocket_thread.start()

    logging.info("Main thread started. WebSocket thread running in background.")
    logging.info("Press CTRL+C to quit.")

    # Keep the main thread alive, otherwise the script would exit immediately
    # as the websocket thread is a daemon.
    try:
        while True:
            # Check if the background thread is still alive
            if not websocket_thread.is_alive():
                logging.error("WebSocket background thread seems to have died unexpectedly. Exiting.")
                break
            # Sleep for a while to avoid busy-waiting
            asyncio.run(asyncio.sleep(5)) # Using asyncio.run here might be complex, maybe just time.sleep
            # import time
            # time.sleep(5)
    except KeyboardInterrupt:
        logging.info("CTRL+C detected. Exiting main thread...")
    except Exception as e:
        logging.error(f"Error in main thread loop: {e}", exc_info=True)
    finally:
        logging.info("Main thread loop finished.")
        # Note: Because the websocket thread is a daemon, it might get cut off abruptly
        # when the main thread exits. Proper shutdown might involve signaling the
        # background thread to close the websocket connection gracefully.