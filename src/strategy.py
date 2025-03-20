# import websockets
# import json
# from config import ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY
# import numpy as np
# import talib
# from datetime import datetime, timezone

# return_dict = {'2025-03-19 13:31:08.907089+00:00': 'long', 'datafeed': []}

# def get_advice():
#     return return_dict

# async def connect_to_websocket():
#     uri = "wss://stream.data.alpaca.markets/v1beta3/crypto/us"
#     async with websockets.connect(uri) as websocket:
#         auth_data = {
#             "action": "auth",
#             "key": ALPACA_PUBLIC_KEY,
#             "secret": ALPACA_SECRET_KEY
#         }
#         await websocket.send(json.dumps(auth_data))

#         subscribe_data = {
#             "action": "subscribe",
#             "bars": ["BTC/USD"]
#         }
#         await websocket.send(json.dumps(subscribe_data))
        
#         # open is a q containing the past 20 minutes of bars
#         open = []

#         # this async function runs everytime it gets a msg
#         async for message in websocket:
#             data = json.loads(message)
#             return_dict['datafeed'] = open
#             # data structure for response messages
#             # [{'T': 'subscription', 'trades': [], 'quotes': [], 'orderbooks': [], 'bars': ['BTC/USD'], 'updatedBars': [], 'dailyBars': []}]
#             # data structure for bars
#             # [{'T': 'b', 'S': 'BTC/USD', 'o': 83833.3295, 'h': 83907.455, 'l': 83833.3295, 'c': 83907.455, 'v': 0, 't': '2025-03-19T11:57:00Z', 'n': 0, 'vw': 83870.39225}]
#             # check if data is bar, if bar, append to queue
#             print(data)
#             if data[0]['T'] == 'b':
#                 if len(open) == 20:
#                     # remove the last element of the list
#                     open.pop()
#                     # get the opening price
#                     open.insert(0, data[0]['o'])
#                 else:
#                     open.insert(0, data[0]['o'])
#                 print(open)
            
            
#             sma10 = talib.SMA(np.array(open), timeperiod=10)
#             sma20 = talib.SMA(np.array(open), timeperiod=20)

#             # get the last element from the respective numpy arrays
#             sma1 = sma10.pop()
#             sma2 = sma20.pop()

#             if sma1 > sma2:
#                 key = datetime.now(timezone.utc)
#                 return_dict[str(key)] = 'short'
#             elif sma1 < sma2:
#                 key = datetime.now(timezone.utc)
#                 return_dict[str(key)] = 'long'

            

import threading
import json
from datetime import datetime, timezone
import numpy as np
import talib
import asyncio
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
