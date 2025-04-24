# %%
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
from prices import get_prices
from prices_helper import prepare_inputs
# due to limitations on a free alpaca plan
# we can only work with live data on 30 tickers
# supported_companies = ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'BRK.B',
#                       'AVGO', 'TSLA', 'JPM', 'LLY', 'V', 'XOM', 'UNH', 'MA',
#                       'NFLX', 'COST', 'PG', 'WMT', 'HD', 'ABBV', 'CVX', 'CRM',
#                       'KO', 'ORCL', 'WFC', 'CSCO', 'PM']
supported_currencies = [
    'BTC/USD',
    'DOGE/USD',
    'ETH/USD',
    'LINK/USD',
    'LTC/USD',
    'SUSHI/USD',
    'UNI/USD',
    'YFI/USD']


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


def CDL2CROWS_strategy(data):
    if (data is None or
            any(k not in data for k in ['open', 'high', 'low', 'close']) or
            len(data['close']) < 3):
        return "HOLD"
    cdl2crows_vals = talib.CDL2CROWS(data['open'], data['high'],
                                     data['low'], data['close'])
    latest_cdl_val = cdl2crows_vals[-1]
    if latest_cdl_val > 0:
        return "BUY"
    if latest_cdl_val < 0:  # Bearish pattern
        return "SELL"  # standard signal
    return "HOLD"


def APO_strategy(data):
    if data is None or 'close' not in data or len(data['close']) < 26:
        return "HOLD"
    apo = talib.APO(data['close'], fastperiod=12, slowperiod=26, matype=0)
    if apo[-1] > 0:
        return "BUY"
    if apo[-1] < 0:
        return "SELL"
    return "HOLD"


def CDLADVANCEBLOCK_strategy(data):
    cdladvanceblock = talib.CDLADVANCEBLOCK(
        data["open"], data["high"], data["low"], data["close"]
    )
    if data is None or len(data['close']) < 3:
        return "HOLD"
    if cdladvanceblock[-1] > 0:
        return "BUY"
    if cdladvanceblock[-1] < 0:
        return "SELL"
    return "HOLD"


def DEMA_strategy(data):
    if data is None or len(data['close']) < 20:
        return "HOLD"
    dema = talib.DEMA(data["close"], timeperiod=30)
    if data['close'][-1] > dema[-1]:
        return "BUY"
    if data['close'][-1] < dema[-1]:
        return "SELL"
    return "HOLD"


def CDL3BLACKCROWS_strategy(data):
    if data is None or len(data['close']) < 3:
        return "HOLD"
    cdl_values = talib.CDL3BLACKCROWS(data['open'], data['high'],
                                      data['low'], data['close'])
    latest_cdl = cdl_values[-1]
    if latest_cdl > 0:
        return "BUY"
    if latest_cdl < 0:
        return "SELL"
    return "HOLD"


def CDLDARKCLOUDCOVER_strategy(data):
    if data is None or len(data['close']) < 3:
        return "HOLD"
    cdl_values = talib.CDLDARKCLOUDCOVER(
        data['open'],
        data['high'],
        data['low'],
        data['close'],
        penetration=0)
    latest_cdl = cdl_values[-1]
    if latest_cdl > 0:
        return "BUY"
    if latest_cdl < 0:
        return "SELL"
    return "HOLD"


def CDLEVENINGDOJISTAR_strategy(data):
    if data is None or len(data['close']) < 3:
        return "HOLD"

    cdl_eveningdoji = talib.CDLEVENINGDOJISTAR(
        data['open'],
        data['high'],
        data['low'],
        data['close'],
        penetration=0)
    latest_cdl = cdl_eveningdoji[-1]
    if latest_cdl > 0:
        return "BUY"
    if latest_cdl < 0:
        return "SELL"
    return "HOLD"


def CDLHANGINGMAN_strategy(data):
    if data is None or len(data['close']) < 3:
        return "HOLD"
    cdl_hanging = talib.CDLHANGINGMAN(data['open'], data['high'],
                                      data['low'], data['close'])
    cdl_hanging = cdl_hanging[-1]
    if cdl_hanging > 0:
        return "BUY"
    if cdl_hanging < 0:
        return "SELL"
    return "HOLD"


def CDLINNECK_strategy(data):
    cdl_linneck = talib.CDLINNECK(
        data["open"],
        data["high"],
        data["low"],
        data["close"])
    if data is None or len(data['close']) < 2:
        return "HOLD"
    cdl_linneck = cdl_linneck[-1]

    if cdl_linneck > 0:
        return "BUY"
    if cdl_linneck < 0:
        return "SELL"
    return "HOLD"


def MACD_strategy(data):
    if data is None or len(data['close']) < 24:
        return "HOLD"
    _, _, macdhist = talib.MACD(
        data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    if macdhist[-1] > 0:
        return "BUY"
    if macdhist[-1] < 0:
        return "SELL"
    return "HOLD"


def RSI_strategy(data):
    if data is None or len(data['close']) < 15:
        return "HOLD"
    rsi = talib.RSI(data['close'], timeperiod=14)
    if rsi[-1] < 30:  # Oversold threshold
        return "BUY"
    if rsi[-1] > 70:  # Overbought threshold
        return "SELL"
    return "HOLD"


def ADX_strategy(data):
    if data is None or len(data['close']) < 27:
        return "HOLD"
    adx = talib.ADX(data['high'], data['low'], data['close'], timeperiod=14)
    plus_di = talib.PLUS_DI(
        data['high'],
        data['low'],
        data['close'],
        timeperiod=14)
    minus_di = talib.MINUS_DI(
        data['high'],
        data['low'],
        data['close'],
        timeperiod=14)
    # Using ADX > 25 for trend strength and comparing DI+ vs DI- for direction
    if adx[-1] > 25 and plus_di[-1] > minus_di[-1]:
        return "BUY"
    if adx[-1] > 25 and minus_di[-1] > plus_di[-1]:
        return "SELL"
    return "HOLD"


def CDLHAMMER_strategy(data):
    if data is None or len(data['close']) < 1:
        return "HOLD"
    cdl_values = talib.CDLHAMMER(
        data['open'],
        data['high'],
        data['low'],
        data['close'])
    latest_cdl = cdl_values[-1]
    if latest_cdl > 0:  # Bullish pattern = +100
        return "BUY"
    if latest_cdl < 0:
        return "SELL"
    # Note: Hammer is Bullish, no inherent SELL signal from this pattern alone
    return "HOLD"


def CDLSHOOTINGSTAR_strategy(data):
    if data is None or len(data['close']) < 1:
        return "HOLD"
    cdl_values = talib.CDLSHOOTINGSTAR(data['open'], data['high'],
                                       data['low'], data['close'])
    latest_cdl = cdl_values[-1]
    if latest_cdl > 0:
        return "BUY"
    if latest_cdl < 0:  # Bearish pattern = -100
        return "SELL"
    return "HOLD"


def HT_PHASOR_strategy(data):
    if data is None or len(data['close']) < 1:
        return "HOLD"
    inphase, _ = talib.HT_PHASOR(data["close"])
    if inphase[-1] < 0:
        return "SELL"
    if inphase[-1] > 0:
        return "BUY"
    return "HOLD"


def HT_SINE_strategy(data):
    if data is None or len(data['close']) < 1:
        return "HOLD"
    sine, _ = talib.HT_SINE(data["close"])
    if sine[-1] > 0:
        return "BUY"
    if sine[-1] < 0:
        return "SELL"
    return "HOLD"


def HT_TRENDLINE_strategy(data):
    if data is None or len(data['close']) < 1:
        return "HOLD"
    ht_trendline = talib.HT_TRENDLINE(data["close"])
    if data['close'][-1] > ht_trendline[-1]:
        return "BUY"
    if data['close'][-1] < ht_trendline[-1]:
        return "SELL"
    return "HOLD"


def KAMA_strategy(data):
    if data is None or len(data['close']) < 30:
        return "HOLD"
    kama = talib.KAMA(data["close"], timeperiod=30)
    if data['close'][-1] > kama[-1]:
        return "BUY"
    if data['close'][-1] < kama[-1]:
        return "SELL"
    return "HOLD"


def MA_strategy(data):
    if data is None or len(data['close']) < 30:
        return "HOLD"
    ma = talib.MA(data["close"], timeperiod=30, matype=0)
    if data['close'][-1] > ma[-1]:
        return "BUY"
    if data['close'][-1] < ma[-1]:
        return "SELL"
    return "HOLD"


def MIDPOINT_strategy(data):
    if data is None or len(data['close']) < 14:
        return "HOLD"
    midpoint = talib.MIDPOINT(data["close"], timeperiod=14)
    if data['close'][-1] > midpoint[-1]:
        return "BUY"
    if data['close'][-1] < midpoint[-1]:
        return "SELL"
    return "HOLD"


def MIDPRICE_strategy(data):
    if data is None or len(data['close']) < 14:
        return "HOLD"
    midprice = talib.MIDPRICE(data["high"], data["low"], timeperiod=14)
    if data['close'][-1] > midprice[-1]:
        return "BUY"
    if data['close'][-1] < midprice[-1]:
        return "SELL"
    return "HOLD"


def SAR_strategy(data):
    if data is None or len(data['close']) < 2:
        return "HOLD"
    sar = talib.SAR(data["high"], data["low"], acceleration=0.02, maximum=0.2)
    if data['close'][-1] > sar[-1]:
        return "BUY"
    if data['close'][-1] < sar[-1]:
        return "SELL"
    return "HOLD"


# ADD HERE
strategies = [
    SMA_MOMENTUM_strategy,
    BBANDS_strategy,
    EMA_strategy,
    VWAP_strategy,
    CDL2CROWS_strategy,
    APO_strategy,
    CDLADVANCEBLOCK_strategy,
    DEMA_strategy,
    CDL3BLACKCROWS_strategy,
    CDLEVENINGDOJISTAR_strategy,
    CDLHANGINGMAN_strategy,
    CDLINNECK_strategy,
    MACD_strategy,
    RSI_strategy,
    ADX_strategy,
    CDLHAMMER_strategy,
    CDLSHOOTINGSTAR_strategy,
    HT_PHASOR_strategy,
    HT_SINE_strategy,
    HT_TRENDLINE_strategy,
    KAMA_strategy,
    MA_strategy,
    MIDPOINT_strategy,
    MIDPRICE_strategy,
    SAR_strategy]

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


def calculate_probabilities(input_dict):
    probabilites_dict = {}
    time_stamp = datetime.now(timezone.utc)
    for instrument in input_dict.keys():
        if len(input_dict[instrument][-1]) != 0:
            buy_percent = count_buy_sell_hold(
                input_dict[instrument][-1], "BUY")
            sell_percent = count_buy_sell_hold(
                input_dict[instrument][-1], "SELL")
            hold_percent = count_buy_sell_hold(
                input_dict[instrument][-1], "HOLD")
            tmp = {
                "buy": buy_percent,
                "sell": sell_percent,
                "hold": hold_percent,
                "time_stamp": time_stamp,
            }

            probabilites_dict[instrument] = tmp

    return probabilites_dict

# """
# RETURN DICT SCHEMA
# {
#     # instrument name
#     ETH/USD: [
#         # each minute, there is a new array, calculated from the prices
#         # comming in from the websocket
#         [
#             # Array of strategy outputs which
#             # looks like the one below
#             {
#                 timestamp: 2025-03-29T08:17:00
#                 strategy_name: SMA_strategy
#                 advice: HOLD
#             }

#         ]
#     ]

# }

# """


return_dict = {}


def get_not_advice():
    return calculate_probabilities(return_dict)

# takes in a string of inputs
# now 100 minutely updates, hour hourly updates, day daily updates, week weekly updates
# input params: Timeframe: <String> (now, hour, day, week)
# return params: ReturnDict: <Dict>
#
# RETURN DICT SCHEMA
# {
#     # instrument name
#     ETH/USD: [
#         # each time frame, there is a new array, calculated from the prices
#         # comming in from the websocket
#         [
#             # Array of strategy outputs which
#             # looks like the one below
#             {
#                 timestamp: 2025-03-29T08:17:00
#                 strategy_name: SMA_strategy
#                 advice: HOLD
#             }
#         ]
#     ]
# }
#


def get_not_advice_v2(tickers, resolution):
    # not advice is already in min
    if resolution == "min":
        return get_not_advice()
    # 100 hours approx 7 days
    if resolution == "hour":
        data = get_prices(tickers, resolution, days_from_now=7)
    # 100 days
    if resolution == "day":
        data = get_prices(tickers, resolution, days_from_now=100)

    time_stamp = datetime.now(timezone.utc)
    result_dict = {}
    for instrument_name in data:
        strat_output_array = []
        bars = data[instrument_name]

        for strat in strategies:
            # abstract function
            talib_input_dict = prepare_inputs(bars)
            strat_output = strat(talib_input_dict)

            formatted_output = format_return_dict(
                time_stamp=time_stamp,
                strategy_name=strat.__name__,
                buy_sell_hold=strat_output,
            )
            strat_output_array.append(formatted_output)

            if instrument_name in result_dict:
                strategies_output = result_dict[instrument_name]
                strategies_output.append(
                    strat_output_array
                )
            else:
                result_dict[instrument_name] = [strat_output_array]

    return calculate_probabilities(result_dict)

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
            if isinstance(data, list) and len(
                    data) > 0 and data[0].get('T') == 'b':
                bar = data[0]
                instrument_name = bar['S']
                # type: [Bars] this only has 1 element so unwrap it
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
                            talib_input_dict = prepare_inputs_live(
                                data_dict[instrument_name])
                            strat_output = strat(talib_input_dict)

                            formatted_output = format_return_dict(
                                time_stamp=time_stamp,
                                strategy_name=strat.__name__,
                                buy_sell_hold=strat_output,
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

# threading.Thread(target=start_websocket_in_background, daemon=True).start()

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
