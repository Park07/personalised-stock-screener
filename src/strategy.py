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
async def bbands_indicator(bars):
    """
    Calculate Bollinger Bands indicator.
    
    Returns:
        "Sell" if current price is above the upper band,
        "Buy" if below the lower band,
        "Hold" otherwise.
    """
    if len(bars) < 20:
        return "Hold"
    close_price = np.array([bar['c'] for bar in bars])
    upper, _, lower = ta.BBANDS(close_price, timeperiod=20)
    current_price = close_price[-1]
    upper_band = upper[-1]
    lower_band = lower[-1]

    # Trading logic
    if current_price > upper_band:
        return "Sell" # Potentially overbought
    if current_price < lower_band:
        return "Buy" # Potentially oversold
    return "Hold" # Within band range

# EMA strategy
async def ema_indicator(bars):
    """
    Calculate Exponential Moving Average (EMA) indicator.
    
    Returns:
        "Buy" if current price is above EMA,
        "Sell" if below EMA,
        "Hold" otherwise.
    """
    if len(bars) < 20:
        return "Hold"

    close_price = np.array([bar['c'] for bar in bars])
    ema = ta.EMA(close_price, timeperiod=20)
    current_price = close_price[-1]
    ema_value = ema[-1]

    if current_price > ema_value:
        return "Buy" # Price above EMA, bullish
    if current_price < ema_value:
        return "Sell" # Price below EMA, bearish
    return "Hold"

# calculate VWAP:
async def vwap_indicator(bars):
    # https://alpaca.markets/learn/algorithmic
    # -trading-with-twap-and-vwap-using-alpaca
    """
    Calculate Volume-Weighted Average Price (VWAP) for stocks.
    
    low + close + high / 3
    """
    if len(bars) < 20:
        return "Hold"

    # Cumulative vwp calculation
    total_volume = 0
    price_volume_sum = 0

    for bar in bars:
        # (H + l + C) / 3
        typical_price = (bar['h'] + bar['l'] + bar['c']) / 3
        volume = bar['v']

        total_volume += volume
        price_volume_sum += typical_price * volume
    # Now calculate vwap
    vwap_value = price_volume_sum / total_volume
    current_price = bars[-1]['c'] # using recent close price, not open oops
    # Determine buying strategy
    if current_price > vwap_value * 1.01:
        return "Buy"
    if current_price < vwap_value * 0.99:
        return "Sell"
    return "Hold"


def get_advice():
    return return_dict

async def connect_to_websocket():
    uri = "wss://stream.data.alpaca.markets/v1beta3/crypto/us"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "action": "auth",
            "key": ALPACA_PUBLIC_KEY,
            "secret": ALPACA_SECRET_KEY
        }))

        subscribe_data = {
            "action": "subscribe",
            "bars": ["BTC/USD"]
        }
        await websocket.send(json.dumps(subscribe_data))
        # using bars now instead of just open
        bars_queue = []
        async for message in websocket:
            data = json.loads(message)
            # make this threadsafe
            return_dict['datafeed'] = bars_queue

            if isinstance(data, list) and len(data) > 0 and data[0].get('T') == 'b':
                bar = data[0]
                if len(bars_queue) == 20:
                    bars_queue.pop()
                bars_queue.insert(0, {
                    'o': bar['o'],
                    'h': bar['h'],
                    'l': bar['l'], 
                    'c': bar['c'],
                    'v': bar['v']
                })
                if len(bars_queue) == 20:
                    bbands_signal = await bbands_indicator(bars_queue)
                    ema_signal = await ema_indicator(bars_queue)
                    vwap_signal = await vwap_indicator(bars_queue)

                    signal_entry = {
                        'timestamp': str(datetime.now(timezone.utc)),
                        'BBANDS': bbands_signal,
                        'EMA': ema_signal,
                        'VWAP': vwap_signal    
                    }

                    return_dict['signals'].append(signal_entry)
                close_price = float(bar.get('c', 0))
                vwap_value = bar.get('vw')
                # VWAP
                if vwap_value is not None:
                    vwap_value = float(vwap_value)

                    if close_price > vwap_value:
                        return_dict['signals'].append({
                            'timestamp': str(datetime.now(timezone.utc)),
                            'signal': 'vwap_buy'
                        })
                    elif close_price < vwap_value:
                        return_dict['signals'].append({
                            'timestamp': str(datetime.now(timezone.utc)),
                            'signal': 'vwap_sell'
                        })
                    else:
                        return_dict['signals'].append({
                            'timestamp': str(datetime.now(timezone.utc)),
                            'signal': 'vwap_hold'
                        })

                # moving avg crossover strat
                # extracting open from the bar?
                if len(bars_queue) == 20:
                    open_prices = np.array([bar['o'] for bar in bars_queue])
                    # sma10 = ta.SMA(np.array(bars_queue), timeperiod=10)
                    sma10 = ta.SMA(open_prices, timeperiod=10)
                    #sma20 = ta.SMA(np.array(bars_queue), timeperiod=20)
                    sma20 = ta.SMA(open_prices, timeperiod=20)

                    if sma10[-1] > sma20[-1]:
                        return_dict['signals'].append({
                            'timestamp': str(datetime.now(timezone.utc)),
                            'signal': 'short'
                        })
                    elif sma10[-1] < sma20[-1]:
                        return_dict['signals'].append({
                            'timestamp': str(datetime.now(timezone.utc)),
                            'signal': 'long'
                        })
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
