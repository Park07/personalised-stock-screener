import requests
BASE_URL = "https://gh4vkppgue.execute-api.us-east-1.amazonaws.com/prod/api/esg/"


def get_esg_indicators(tickers):
    res_dict = {}
    for ticker in tickers:
        data = requests.get(f'{BASE_URL}{ticker}')
        if data.status_code == 200:
            res_dict[ticker] = data.json()
    return res_dict
