import numpy as np
import pandas as pd
# import talib
from .prices import get_indicators
import xgboost as xgb

from .prices_helper import validate_crypto_trading_pairs

CRYPTO = ['BTC/USD', 'DOGE/USD', 'ETH/USD', 'LINK/USD', 'LTC/USD',
          'SUSHI/USD', 'UNI/USD', 'YFI/USD']

# helper fcuntion, gets the snp500
def get_snp_100():
    tickers = pd.read_csv('tickers.csv')
    tickers_list = tickers[' Symbol'].to_list()
    return tickers_list[:100]
# no input
# returns a list of talib function naems for the abstract function
def talib_func_groups():
    func_groups = talib.get_function_groups()

    # remove these ones cus they are useless
    # not really suitiable to be "features"
    func_groups.pop('Math Operators')
    func_groups.pop('Math Transform')

    feature_name_list = []
    for group in func_groups:
        feature_name_list = feature_name_list + func_groups[group]

    # remove this feature cus its causing errors
    feature_name_list.remove('MAVP')

    return feature_name_list


# ticker str, ticker for the instrument
#
# resolution is minute hour or days
def format_data(ticker, resolution):
    feature_names_list = talib_func_groups()
    if resolution == 'day':
        data = get_indicators([ticker], feature_names_list, 1000, resolution)
    elif resolution == 'hour':
        data = get_indicators([ticker], feature_names_list, 90, resolution)
    elif resolution == 'min':
        data = get_indicators([ticker], feature_names_list, 3, resolution)
    else:
        data = get_indicators([ticker], feature_names_list, 3, resolution)

    # df list for concatenation
    # format the inputs for the model
    df_list = []
    labels_list = []
    for instrument in data['stock_data'].keys():
        df = pd.DataFrame.from_records(data['stock_data'][instrument])
        # normalize label
        label = df['open'].pct_change().shift(6)
        # drop the first 50 rows to avoid nans
        label = label.iloc[100:]
        df = df.iloc[100:]
        # append to respective lists
        labels_list.append(label)
        df_list.append(df)
    features = pd.concat(df_list)
    features = features.set_index(['symbol', 'timestamp']).astype(float)
    labels = pd.concat(labels_list)
    return features, labels


# features is a dataframe with columns features and rows instruments
# labels is the opening price, rolled back 5 time incriments
# name of the model weights
# returns the model weights so that they can be loaded
def train_model(features, labels, name, resolution):
# DO NOT RUN THIS ON THE SEVRER DO NOT RUN THIS ON THE SERVER DO NOT RUN THIS ON THE SERVER

# THIS WILL USE UP ALL OUR CREDITS AND WE WILL GO INTO DEBT
    model = xgb.XGBRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=64,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=694201337,
        verbosity=1
    )
    model.fit(
        features, labels,
    )
    if validate_crypto_trading_pairs([name]):
        coin_name = name.split('/')
        name = coin_name[0]
    model_name = f'models/{str(name)}_{str(resolution)}.json'
    model.save_model(model_name)

def get_prediction(ticker, resolution):
    # dont need labels we aint training
    features, _ = format_data(ticker, resolution)
    # constructs a file name model name to load from the models folder
    if validate_crypto_trading_pairs([ticker]):
        coin_name = ticker.split('/')
        ticker = coin_name[0]
    model_name = f'models/{str(ticker)}_{str(resolution)}.json'

    model = xgb.XGBRegressor()
    model.load_model(model_name)
    y_pred = model.predict(features)
    res = {
        "pred": round(float(y_pred[-1]) * 100, 5)
    }

    return res