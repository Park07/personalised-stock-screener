import threading
import json
from datetime import datetime, timezone
import asyncio
import numpy as np
import talib as ta
import websockets
from config import ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY
import pandas as pd

return_dict = {'datafeed': []}

# strategies: BBAnds, EMA, VWAP et
def BBANDS_indicator(tickers, data, time_period, resolution):
    """ Bollinger bands indicators """
    upper, middle, lower = ta.BBANDS(data["Close"], time_period=time_period)
    current_price = data["Close"].iloc[-1]
    upper_band = upper.iloc[-1]
    lower_band = lower.iloc[-1]

    # Trading logic
    if current_price > upper_band:
        return "Sell" # Potentially overbought
    elif current_price < lower_band:
        return "Buy" # Potentially oversold
    else:
        return "Hold" # Within band range

# EMA strategy
def EMA_indicator(tickers, data, time_period, resolution):
    """data = dataframe from panda library"""

    ema = ta.EMA(data["Close"], time_period=time_period)
    current_price = data["Close"].iloc[-1]
    ema_value = ema.iloc[-1]

    if current_price > ema_value:
        return "Buy" # Price above EMA, bullish
    elif current_price < ema_value:
        return "Sell" # Price below EMA, bearish
    else:
        return "Hold"
# calculate VWAP:
def VWAP_stock_indicator(tickers, data, time_period, resolution):
    if len(data) < time_period:
        return "Hold"

    # Considering only recent time_period
    recent_data = data.iloc[-time_period:]

    # Formula (High + Low + close) / 3
    typical_price = (recent_data["High"] + recent_data["Low"] + recent_data["Close"])/ 3

    # Add weights
    vwap_value = (typical_price * recent_data["Volume"]).sum() / recent_data["Volume"].sum()

    # Get the last closing price
    current_price = data["Close"].iloc[-1]

    # Determine buying strategy
    if current_price > vwap_value:
        return "Buy"
    elif current_price < vwap_value:
        return "Sell"
    else:
        return "Hold"


# VWAP: Stocks calculating

    
def get_advice():
    return return_dict

async def connect_to_websocket():
    uri = "wss://stream.data.alpaca.markets/v1beta3/crypto/us"
    async with websockets.connect(uri) as websocket:
        auth_data = {
            "action": "auth",
            "key": ALPACA_PUBLIC_KEY,
            "secret": ALPACA_SECRET_KEY
        }
        await websocket.send(json.dumps(auth_data))

        subscribe_data = {
            "action": "subscribe",
            "bars": ["BTC/USD"]
        }
        await websocket.send(json.dumps(subscribe_data))
        # open prices queue
        open_prices = []

        async for message in websocket:
            data = json.loads(message)
            # make this threadsafe
            return_dict['datafeed'] = open_prices

            if isinstance(data, list) and len(data) > 0 and data[0].get('T') == 'b':
                bar = data[0]
                if len(open_prices) == 20:
                    open_prices.pop()
                open_prices.insert(0, data[0]['o'])
                close_prices = bar.get('c')
                vwap_values = bar.get('vw')

                # VWAP
                if vwap_values is not None:
                    if close_prices > vwap_values:
                        return_dict[str(datetime.now(timezone.utc))] = 'vwap_buy'
                    elif close_prices < vwap_values:
                        return_dict[str(datetime.now(timezone.utc))] = 'vwap_sell'
                    else:
                        return_dict[str(datetime.now(timezone.utc))] = 'vwap_hold'

                # moving avg crossover strat
                if len(open_prices) == 20:
                    sma10 = ta.SMA(np.array(open_prices), timeperiod=10)
                    sma20 = ta.SMA(np.array(open_prices), timeperiod=20)

                    if sma10[-1] > sma20[-1]:
                        return_dict[str(datetime.now(timezone.utc))] = 'short'
                    elif sma10[-1] < sma20[-1]:
                        return_dict[str(datetime.now(timezone.utc))] = 'long'

async def run_websocket():
    while True:
        try:
            await connect_to_websocket()
        except Exception as e:
            print(f"WebSocket Error: {e}")
            await asyncio.sleep(5)  # Retry delay

def start_websocket_in_background():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_websocket())

# Start WebSocket in a separate thread
threading.Thread(target=start_websocket_in_background, daemon=True).start()
