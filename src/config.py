import os
from dotenv import load_dotenv

# Usage
# Sign up to the apis listed below, get a key.
# echo "export ALPACA_SECRET_KEY='apikeyhere'" >> ~/.bashrc

ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", None)
ALPACA_PUBLIC_KEY = os.getenv("ALPACA_PUBLIC_KEY", None)
FMP_API_KEY = os.getenv("FMP_API_KEY", None)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", None)

# AWS RDS PostgreSQL Configuration
RDS_HOST = os.getenv('RDS_HOST')
RDS_PORT = os.getenv('RDS_PORT', '5432')
RDS_DB_NAME = os.getenv('RDS_DB_NAME', 'stock_screener')
RDS_USERNAME = os.getenv('RDS_USERNAME')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')

# Database URLs
DATABASE_URL = f"postgresql://{RDS_USERNAME}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/{RDS_DB_NAME}"


# using sqlite for storing table of companies
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'metrics_cache.sqlite')
