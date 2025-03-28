import threading
import json
from datetime import datetime, timezone
import asyncio
import numpy as np
import talib
import websockets
import logging
from .config import ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY

# due to limitations on a free alpaca plan
# we can only work with live data on 30 tickers
# supported_companies = ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'BRK.B', 'AVGO', 'TSLA', 'JPM', 'LLY', 'V', 'XOM', 'UNH', 'MA', 'NFLX', 'COST', 'PG', 'WMT', 'HD', 'ABBV', 'CVX', 'CRM', 'KO', 'ORCL', 'WFC', 'CSCO', 'PM']
supported_currencies = ["BTC/USD", 'DOGE/USD', 'ETH/USD', 'LINK/USD', 'LTC/USD', 'SUSHI/USD', 'UNI/USD', 'YFI/USD']

def SMA_MOMENTUM_strategy(data):
    inputs = prepare_inputs_live(data)

    # moving avg momentum strat
    if len(inputs['open']) > 20:
        sma10 = talib.SMA(inputs, timeperiod=10)
        sma20 = talib.SMA(inputs, timeperiod=20)

        if sma10[-1] > sma20[-1]:
            return 'BUY'
        elif sma10[-1] < sma20[-1]:
            return 'SELL'
    else:
        return 'HOLD'
    
def BBANDS_strategy(data):
    input = prepare_inputs_live(data)
    upper, _, lower = talib.BBANDS(input, timeperiod=20)
    if input is None or input['close'] < 20:
        return "HOLD"

    if input['close'][-1] > upper[-1]:
        return "SELL"
    elif input['close'][-1] < lower[-1]:
        return "BUY"
    return "HOLD"


def EMA_strategy(data):
    inputs = prepare_inputs_live(data)
    if inputs is None or len(inputs['close']) < 20:
        return "HOLD"
    
    ema = talib.EMA(inputs['close'], timeperiod=30)
    if inputs['close'][-1] > ema[-1]:
        return "BUY"
    elif inputs['close'][-1] < ema[-1]:
        return "SELL"
    return "HOLD"



# ADD FUNCTION NAME HERE
strategies = [SMA_MOMENTUM_strategy,BBANDS_strategy, EMA_strategy]

return_dict = {}
def get_advice():
    return return_dict

# THIS FUNCTION IS NOT THREAD SAFE. MUST BE SINGLE THREADED
async def connect_to_websocket():
    # SCHEMA
    # INSTRUMENT_NAME: LIST<BARS>
    data_dict = {}

    # uri = "wss://stream.data.alpaca.markets/v2/iex"
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
            "bars": supported_currencies
        }
        await websocket.send(json.dumps(subscribe_data))

        # this should run every single minute
        async for message in websocket:
            data = json.loads(message)

            # DEBUGGING
            print(data)
            print(data_dict)
            print(return_dict)

            # data schema:
            # T: type
            # S: Name of instrument
            # o: opening price
            # h: high
            # l: low
            # c: close
            # v: volume
            # t: time stamp
            # n: no idea but apprently its always 0????
            # vw: no idea same as n

            # this is NOT threadsafe, this function needs to be single threaded
            # need to add a lock to this

            # circular queue
            if isinstance(data, list) and len(data) > 0 and data[0].get('T') == 'b':
                # type: [Bars] this only has 1 element so unwrap it
                bar = data[0]
                instrument_name = bar['S']
                
                # circular queue logic
                if instrument_name in data_dict:
                    print("hi")
                    data_dict[instrument_name].append(bar)
                    if len(data_dict[instrument_name]) == 100:
                        data_dict[instrument_name].pop(0)
                else:
                    print("hi")
                    # stick the empty list in
                    data_dict[instrument_name] = data

                print(data_dict)

                time_stamp = datetime.now(timezone.utc)
                
                for instrument_name in supported_currencies:
                    if instrument_name in data_dict:
                        for strat in strategies:
                            # abstract function, loops through a list of functions defined by list: STRATEGIES
                            sma_output = strat(data_dict[instrument_name])

                            formatted_output = format_return_dict(
                                time_stamp =time_stamp, 
                                strategy_name =strat.__name__,
                                buy_sell_hold = sma_output,
                            )

                            if instrument_name in return_dict:
                                strategies_output = return_dict[instrument_name]
                                strategies_output.append(
                                    formatted_output
                                )
                            else:
                                return_dict[instrument_name] = [formatted_output]

def format_return_dict(time_stamp, strategy_name, buy_sell_hold):
    new_element = {
        # Datetime object: time stamp
        "time_stamp": time_stamp,
        # String: name of strategy
        "strategy_name": str(strategy_name),
        # String: buy, sell, hold
        "advice": str(buy_sell_hold),
    }
    
    return new_element

async def run_websocket():
    
    while True:
        await connect_to_websocket()

# helper to generate a inputs dictionary
def prepare_inputs_live(stock_bars):
    """
    takes in a dictionary of stock bars. and formats them for inputting into the TAlib
    abstract function
    
    :param stock bars: a dictionary [{open,high,low,close,volume}]
    :return: dict of ndarrays with the following keyys {open:[],high:[],low:[],close:[],volume:[]}
    """

    try:
        # init everything
        open = np.array([])
        high = np.array([])
        low = np.array([])
        close = np.array([])
        volume = np.array([])

        for bar in stock_bars:
            # init inputs dict
            open = np.append(open, bar['o'])
            high = np.append(high, bar['h'])
            low = np.append(low, bar['l'])
            close = np.append(close, bar['c'])
            volume = np.append(volume, bar['v'])

        # place into input dict
        inputs = {
            'open': np.array(open),
            'high': np.array(high),
            'low': np.array(low),
            'close': np.array(close),
            'volume': np.array(volume)
        }

        return inputs
    except Exception as e:
        logging.error(f"Error: error processcing inputs for talib: %s", e)
        return

def start_websocket_in_background():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_websocket())


# threading.Thread(target=start_websocket_in_background, daemon=True).start()

# TESTING ONLY DO NOT UNCOMMENT FOR PROD
if __name__ == "__main__":
    threading.Thread(target=start_websocket_in_background, daemon=True).start()
    
    # Prevent script from exiting
    while True:
        try:
            asyncio.run(asyncio.sleep(1))  # Keep the main thread alive
        except KeyboardInterrupt:
            print("Exiting...")
            break