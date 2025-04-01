import threading
import json
from datetime import datetime, timezone
import asyncio
import logging
import numpy as np
import talib
import talib.abstract
import websockets
from config import ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY

# due to limitations on a free alpaca plan
# we can only work with live data on 30 tickers
# supported_companies = ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'BRK.B',
#                       'AVGO', 'TSLA', 'JPM', 'LLY', 'V', 'XOM', 'UNH', 'MA',
#                       'NFLX', 'COST', 'PG', 'WMT', 'HD', 'ABBV', 'CVX', 'CRM',
#                       'KO', 'ORCL', 'WFC', 'CSCO', 'PM']
supported_currencies = ["BTC/USD", 'DOGE/USD', 'ETH/USD', 'LINK/USD', 'LTC/USD',
                        'SUSHI/USD', 'UNI/USD', 'YFI/USD']

def SMA_MOMENTUM_strategy(data):
    sma = talib.abstract.SMA
    # moving avg momentum strat
    if len(data['open']) > 20:
        sma10 = sma(data, timeperiod=10)
        sma20 = sma(data, timeperiod=20)

        if sma10[-1] > sma20[-1]:
            return 'BUY'
        if sma10[-1] < sma20[-1]:
            return 'SELL'
    return 'HOLD'


def BBANDS_strategy(data):
    bbands = talib.abstract.BBANDS

    if data is None or len(data['close']) < 20:
        return "HOLD"
    upper, _, lower = bbands(data, timeperiod=20)
    if data['close'][-1] > upper[-1]:
        return "SELL"
    if data['close'][-1] < lower[-1]:
        return "BUY"
    return "HOLD"


def EMA_strategy(data):
    ema = talib.abstract.EMA
    if data is None or len(data['close']) < 20:
        return "HOLD"

    ema_res = ema(data['close'], timeperiod=30)
    if data['close'][-1] > ema_res[-1] * 1.01:
        return "BUY"
    if data['close'][-1] < ema_res[-1] * 0.99:
        return "SELL"
    return "HOLD"

def VWAP_strategy(data):
    """
    ( high + Low + Close ) / 3
    """
    if data is None or len(data['close']) < 20:
        return "HOLD"

    typical_price = data['high'] + data['low'] + data['close']
    vwap = np.sum(typical_price * data['volume']) / np.sum(data['volume'])

    latest_close = data['close'][-1]

    if latest_close > vwap * (1.03):
        return "BUY"
    if latest_close < vwap * (0.97):
        return "SELL"
    return "HOLD"
# ADD FUNCTION NAME HERE
strategies = [SMA_MOMENTUM_strategy, BBANDS_strategy, EMA_strategy, VWAP_strategy]

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
    count = 0
    for element in return_dict_slice:
        if element["advice"] == x:
            count += 1
    
    return (count / len(return_dict_slice)) * 100

def calculate_probabilities():
    probabilites_dict = {}
    time_stamp = datetime.now(timezone.utc)
    for currency in supported_currencies:
        if len(return_dict[currency][-1]) != 0:
            buy_percent = count_buy_sell_hold(return_dict[currency][-1], "BUY")
            sell_percent = count_buy_sell_hold(return_dict[currency][-1], "SELL")
            hold_percent = count_buy_sell_hold(return_dict[currency][-1], "HOLD")
            tmp = {
                "buy": buy_percent,
                "sell": sell_percent,
                "hold": hold_percent,
                "time_stamp": time_stamp,
            }

            probabilites_dict[currency] = tmp

    return probabilites_dict

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

return_dict = {}
def get_advice():
    return calculate_probabilities()

# THIS FUNCTION IS NOT THREAD SAFE. MUST BE SINGLE THREADED
async def connect_to_websocket():
    # SCHEMA
    # INSTRUMENT_NAME: LIST<BARS>
    data_dict = {}

    # uri = "wss://stream.data.alpaca.markets/v2/iex"
    uri = "wss://stream.data.alpaca.markets/v1beta3/crypto/us"
    async with websockets.connect(uri) as websocket:
        logging.info("Authenticating with Alpaca")
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
            logging.info("Incomming price update from Alpaca")
            data = json.loads(message)

            # DEBUGGING
            # print(data)
            # print(data_dict)
            # print(return_dict)
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
                    data_dict[instrument_name].append(bar)
                    if len(data_dict[instrument_name]) == 100:
                        data_dict[instrument_name].pop(0)
                else:
                    # stick the empty list in
                    data_dict[instrument_name] = data

                time_stamp = datetime.now(timezone.utc)

                for instrument_name in supported_currencies:
                    if instrument_name in data_dict:

                        strat_output_array = []
                        for strat in strategies:

                            # abstract function, loops through a list of functions
                            # defined by list: STRATEGIES
                            talib_input_dict = prepare_inputs_live(data_dict[instrument_name])
                            strat_output = strat(talib_input_dict)

                            formatted_output = format_return_dict(
                                time_stamp =time_stamp,
                                strategy_name =strat.__name__,
                                buy_sell_hold = strat_output,
                            )

                            strat_output_array.append(formatted_output)

                        if instrument_name in return_dict:
                            strategies_output = return_dict[instrument_name]
                            strategies_output.append(
                                strat_output_array
                            )
                        else:
                            return_dict[instrument_name] = [strat_output_array]
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
    logging.info("Web socket listen thread started")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_websocket())

threading.Thread(target=start_websocket_in_background, daemon=True).start()

# TESTING ONLY COMMENT OUT FOR PROD
# if __name__ == "__main__":
#     threading.Thread(target=start_websocket_in_background, daemon=True).start()
    
#     # Prevent script from exiting
#     while True:
#         try:
#             asyncio.run(asyncio.sleep(1))  # Keep the main thread alive
#         except KeyboardInterrupt:
#             print("Exiting...")
#             break