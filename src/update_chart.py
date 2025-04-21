# populating SQLIte cache
# python3 update_chart.py => i might just run it once cos it's close to due date

import sqlite3
from psycopg2.extras import execute_values 
import time
import logging
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import os

from fundamentals import (
    get_profile, get_ratios, get_key_metrics, get_growth, get_ev_ebitda 
)
from database import get_sqlite_connection 
from config import SQLITE_DB_PATH
from company_data import STOCK_UNIVERSE

API_DELAY_SECONDS = 0.75 
DB_TABLE_NAME = "stock_metrics_cache"
logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s-%(message)s')

def normalise_rating(rating_text):
    if not rating_text: return None
        rating_map = {'strong_buy': 5.0, 'buy': 4.0, 'hold': 3.0, 'underperform': 2.0, 'sell': 1.0}
        return rating_map.get(rating_text.lower().replace(' ', '_'), 3.0)
