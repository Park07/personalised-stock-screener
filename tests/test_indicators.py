import requests
import pytest

BASE_URL = "http://127.0.0.1:5000"

# test cases
overlap_studies = (
    "BBANDS,DEMA,EMA,HT_TRENDLINE,KAMA,MA,MAMA,MAVP,MIDPOINT,MIDPRICE,"
    "SAR,SAREXT,SMA,T3,TEMA,TRIMA,WMA"
)
momentums = (
    "ADX,ADXR,APO,AROON,AROONOSC,BOP,CCI,CMO,DX,MACD,MACDEXT,MACDFIX,MFI,"
    "MINUS_DI,MINUS_DM,MOM,PLUS_DI,PLUS_DM,PPO,ROC,ROCP,ROCR,ROCR100,RSI,"
    "STOCH,STOCHF,STOCHRSI,TRIX,ULTOSC,WILLR"
)

volumes = "AD,ADOSC,OBV"

cycles = "HT_DCPERIOD,HT_DCPHASE,HT_PHASOR,HT_SINE,HT_TRENDMODE"

price_transforms = "AVGPRICE,MEDPRICE,TYPPRICE,WCLPRICE"

volatilities = "ATR,NATR,TRANGE"

pattern_recognition = (
    "CDL2CROWS,CDL3BLACKCROWS,CDL3INSIDE,CDL3LINESTRIKE,CDL3OUTSIDE,"
    "CDL3STARSINSOUTH,CDL3WHITESOLDIERS,CDLABANDONEDBABY,CDLADVANCEBLOCK,"
    "CDLBELTHOLD,CDLBREAKAWAY,CDLCLOSINGMARUBOZU"
)

statistical_functions = (
    "BETA,CORREL,LINEARREG,LINEARREG_ANGLE,LINEARREG_INTERCEPT,"
    "LINEARREG_SLOPE,STDDEV,TSF,VAR"
)
def overlap_studies_cases(overlap_studies):
    res = requests.get(
        f"{BASE_URL}/indicators={overlap_studies}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200

def momentums_cases(momentums):
    res = requests.get(
        f"{BASE_URL}/indicators={momentums}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200


def volumes_cases(volumes):
    res = requests.get(
        f"{BASE_URL}/indicators={volumes}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200


def cycles_cases(cycles):
    res = requests.get(
        f"{BASE_URL}/indicators={cycles}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200


def price_transforms_cases(price_transforms):
    res = requests.get(
        f"{BASE_URL}/indicators={price_transforms}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200
def volatilitys_cases(volatilities):
    res = requests.get(
        f"{BASE_URL}/indicators={volatilities}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200

def pattern_recognition_cases(pattern_recognition):
    res = requests.get(
        f"{BASE_URL}/indicators={pattern_recognition}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200


def statistical_functions_cases(statistical_functions):
    res = requests.get(
        f"{BASE_URL}/indicators={statistical_functions}"
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code == 200

# Sanity check, This should throw an exception
def invalid_inputs_case():
    res = requests.get(
        f"{BASE_URL}AKJSLDKJALKSJLDJLKAKJSLDKJALKSJD="
        "?tickers=ETH/USD&indicators=BBANDS&time_period=7&resolution=min")
    assert res.status_code != 200

if __name__ == "__main__":
    pattern_recognition_cases(pattern_recognition)
    volatilitys_cases(volatilities)
    price_transforms_cases(price_transforms)
    cycles_cases(cycles)
    volumes_cases(volumes)
    momentums_cases(momentums)
    overlap_studies_cases(overlap_studies)
    statistical_functions_cases(statistical_functions)
    invalid_inputs_case()
