import requests
BASE_URL = "http://35.169.25.122"
# BASE_URL = "http://127.0.0.1:5000"


def test_esg_indicators():
    """Test the external ESG api from SIEERA"""
    res = requests.get(f"{BASE_URL}/indicators_esg?tickers=AAPL")
    assert res.status_code == 200
    with open('tests/esg_test.json', 'r', encoding='utf-8') as file:
        data = file.read()
    assert str(res.json()) == str(data)
