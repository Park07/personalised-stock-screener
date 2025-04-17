import requests
BASE_URL = "http://35.169.25.122"
# BASE_URL = "http://127.0.0.1:5000"
def test_advice():
    """Test the external ESG api from SIEERA"""
    res = requests.get(f"{BASE_URL}/analysis_v1")
    assert res.status_code == 200
