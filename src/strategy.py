import threading
import json
from datetime import datetime, timezone
import asyncio
import numpy as np
import talib
import websockets
from config import ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY

return_dict = {'datafeed': []}

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
                if len(open_prices) == 20:
                    open_prices.pop()
                open_prices.insert(0, data[0]['o'])

                # moving avg crossover strat
                if len(open_prices) == 20:
                    sma10 = talib.SMA(np.array(open_prices), timeperiod=10)
                    sma20 = talib.SMA(np.array(open_prices), timeperiod=20)

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
