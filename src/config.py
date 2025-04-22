import os

# Usage
# Sign up to the apis listed below, get a key.
# echo "export ALPACA_SECRET_KEY='apikeyhere'" >> ~/.bashrc

ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", None)
ALPACA_PUBLIC_KEY = os.getenv("ALPACA_PUBLIC_KEY", None)
FMP_API_KEY = os.getenv("FMP_API_KEY", None)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", None)

# using sqlite for storing table of companies
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'metrics_cache.sqlite')
