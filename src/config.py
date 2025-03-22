import os

# Usage
# Sign up to the apis listed below, get a key.
# echo "export ALPACA_SECRET_KEY='apikeyhere'" >> ~/.bashrc

ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", None)
ALPACA_PUBLIC_KEY = os.getenv("ALPACA_PUBLIC_KEY", None)
FMP_API_KEY = os.getenv("FMP_API_KEY", None)
