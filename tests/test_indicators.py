"""
This module contains tests for the financial indicators API.

It verifies that the API correctly handles different types of technical indicators,
such as overlap studies, momentum indicators, volume indicators, and more.
"""

import requests

BASE_URL = "http://35.169.25.122"

'''
    "BBANDS,DEMA,EMA,HT_TRENDLINE,KAMA,MA,MAMA,MAVP,MIDPOINT,MIDPRICE,"
    "SAR,SAREXT,SMA,T3,TEMA,TRIMA,WMA"
'''
# test cases
overlap_studies = (
    "BBANDS, EMA, VWAP"
)

momentums = (
    "ADX,ADXR,APO,AROON,AROONOSC,BOP,CCI,CMO,DX,MACD,MACDEXT,MACDFIX,MFI,"
    "MINUS_DI,MINUS_DM,MOM,PLUS_DI,PLUS_DM,PPO,ROC,ROCP,ROCR,ROCR100,RSI,"
    "STOCH,STOCHF,STOCHRSI,TRIX,ULTOSC,WILLR"
)

VOLUMES = "AD,ADOSC,OBV"

CYCLES = "HT_DCPERIOD,HT_DCPHASE,HT_PHASOR,HT_SINE,HT_TRENDMODE"

PRICE_TRANSFORM = "AVGPRICE,MEDPRICE,TYPPRICE,WCLPRICE"

VOLATILITIES = "ATR,NATR,TRANGE"

PATTERN_RECOGNITION = (
    "CDL2CROWS,CDL3BLACKCROWS,CDL3INSIDE,CDL3LINESTRIKE,CDL3OUTSIDE,"
    "CDL3STARSINSOUTH,CDL3WHITESOLDIERS,CDLABANDONEDBABY,CDLADVANCEBLOCK,"
    "CDLBELTHOLD,CDLBREAKAWAY,CDLCLOSINGMARUBOZU"
)

STATISTICAL_FUNCTIONS = (
    "BETA,CORREL,LINEARREG,LINEARREG_ANGLE,LINEARREG_INTERCEPT,"
    "LINEARREG_SLOPE,STDDEV,TSF,VAR"
)

def test_overlap_studies_cases():
    """Test the API with overlap studies indicators to ensure it returns a 200 status."""
    res = requests.get(
        f"{BASE_URL}/indicators={OVERLAP_STUDIES}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200

def test_momentums_cases():
    """Test the API with momentum indicators to ensure it returns a 200 status."""
    res = requests.get(
        f"{BASE_URL}/indicators={MOMENTUMS}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200


def test_volumes_cases():
    """Test the API with volume indicators to ensure it returns a 200 status."""
    res = requests.get(
        f"{BASE_URL}/indicators={VOLUMES}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200


def test_cycles_cases():
    """Test the API with cycle indicators to ensure it returns a 200 status."""
    res = requests.get(
        f"{BASE_URL}/indicators={CYCLES}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200


def test_price_transforms_cases():
    """Test the API with price transformation indicators to ensure it returns a 200 status."""
    res = requests.get(
        f"{BASE_URL}/indicators={PRICE_TRANSFORM}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200


def test_volatilitys_cases():
    """Test the API with volatility indicators to ensure it returns a 200 status."""
    res = requests.get(
        f"{BASE_URL}/indicators={VOLATILITIES}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200

def test_pattern_recognition_cases():
    """Test the API with pattern recognition indicators to ensure it returns a 200 status."""
    res = requests.get(
        f"{BASE_URL}/indicators={PATTERN_RECOGNITION}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200


def test_statistical_functions_cases():
    """Test the API with statistical function indicators to ensure it returns a 200 status."""
    res = requests.get(
        f"{BASE_URL}/indicators={STATISTICAL_FUNCTIONS}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200

# # Sanity check, This should throw an exception
# def invalid_inputs_case():
#     res = requests.get(
#         f"{BASE_URL}/AKJSLDKJALKSJLDJLKAKJSLDKJALKSJD="
#         "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
#     print(res)
#     assert res.status_code != 200

# if __name__ == "__main__":
#     pattern_recognition_cases(PATTERN_RECOGNITION)
#     volatilitys_cases(VOLATILITIES)
#     price_transforms_cases(PRICE_TRANSFORM)
#     cycles_cases(CYCLES)
#     volumes_cases(VOLUMES)
#     momentums_cases(MOMENTUMS)
#     overlap_studies_cases(OVERLAP_STUDIES)
#     statistical_functions_cases(STATISTICAL_FUNCTIONS)
#     invalid_inputs_case()
