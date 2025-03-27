"""
Module: strategy
Retrieves historical stock or crypto data from Alpaca and calculates 
technical indicators.
"""
import threading
import json
from datetime import datetime, timezone
import asyncio
import numpy as np
import talib as ta
import websockets
from config import ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY

return_dict = {
    'datafeed': [],
    'signals': []
    }

# strategies: BBAnds, EMA, VWAP et
async def bbands_indicator(open_prices):
    """
    Calculate Bollinger Bands indicator.
    
    Returns:
        "Sell" if current price is above the upper band,
        "Buy" if below the lower band,
        "Hold" otherwise.
    """
    if len(open_prices) < 20:
        return "Hold"
    
    close_prices = np.array(open_prices)
    upper, _, lower = ta.BBANDS(close_prices, timeperiod=20)
    current_price = close_prices[-1]
    upper_band = upper[-1]
    lower_band = lower[-1]

    # Trading logic
    if current_price > upper_band:
        return "Sell" # Potentially overbought
    if current_price < lower_band:
        return "Buy" # Potentially oversold
    return "Hold" # Within band range

# EMA strategy
async def ema_indicator(open_prices):
    """
    Calculate Exponential Moving Average (EMA) indicator.
    
    Returns:
        "Buy" if current price is above EMA,
        "Sell" if below EMA,
        "Hold" otherwise.
    """
    if len(open_prices) < 20:
        return "Hold"

    close_prices = np.array(open_prices)
    ema = ta.EMA(close_prices, timeperiod=20)
    current_price = close_prices[-1]
    ema_value = ema[-1]

    if current_price > ema_value:
        return "Buy" # Price above EMA, bullish
    if current_price < ema_value:
        return "Sell" # Price below EMA, bearish
    return "Hold"

# calculate VWAP:
async def vwap_stock_indicator(open_prices):
    """
    Calculate Volume-Weighted Average Price (VWAP) for stocks.
    
    Returns:
        "Buy" if current price is above VWAP,
        "Sell" if below VWAP,
        "Hold" otherwise.
    """
    if len(open_prices) < 20:
        return "Hold"

    close_prices = np.array(open_prices)

    # Typical price calculation
    typical_price = close_prices

    # Simplified VWAP calculation (since we only have prices)
    vwap_value = np.mean(typical_price)

    # Get the last closing price
    current_price = close_prices[-1]

    # Determine buying strategy
    if current_price > vwap_value:
        return "Buy"
    if current_price < vwap_value:
        return "Sell"
    return "Hold"


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
                    
                if len(open_prices) == 20:
                    bbands_signal = await bbands_indicator(open_prices)
                    ema_signal = await ema_indicator(open_prices)
                    vwap_signal = await vwap_indicator(open_prices)

                    return_dict['signals'] = {
                        'timestamp': str(datetime.now(timezone.utc)),
                        'BBANDS': bbands_signal,
                        'EMA': ema_signal,
                        'VWAP': vwap_signal    
                    }
                

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
