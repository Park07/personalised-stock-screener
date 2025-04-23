# populating SQLIte cache
# python3 update_chart.py => i might just run it once cos it's close to
# due date

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
    get_profile, get_ratios, get_key_metrics, get_growth
)
from .database import get_sqlite_connection
from ..config import SQLITE_DB_PATH
from ..company_data import STOCK_UNIVERSE

API_DELAY_SECONDS = 0.75
DB_TABLE_NAME = "stock_metrics_cache"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s-%(levelname)s-%(message)s')


def normalise_rating(rating_text):
    if not rating_text:
        return None
    rating_map = {
        'strong_buy': 5.0,
        'buy': 4.0,
        'hold': 3.0,
        'underperform': 2.0,
        'sell': 1.0}
    return rating_map.get(rating_text.lower().replace(' ', '_'), 3.0)


def ensure_db_table_exists(conn):
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {DB_TABLE_NAME} (
            ticker TEXT PRIMARY KEY,
            company_name TEXT,
            sector TEXT,
            market_cap REAL,
            current_price REAL,
            pe_ratio REAL,
            roe REAL,
            dividend_yield REAL,
            debt_equity_ratio REAL,
            revenue_growth REAL,
            earnings_growth REAL,
            last_updated TEXT
        )""")
        conn.commit()
    finally:
        cursor.close()


def fetch_and_process_ticker(ticker):
    logging.debug(f"Processing {ticker}...")
    data = {'ticker': ticker}
    try:
        profile = get_profile(ticker)
        if not profile:
            return None
        ratios = get_ratios(ticker) or {}
        growth = get_growth(ticker) or {}

        data['company_name'] = profile.get('companyName')
        data['sector'] = profile.get('sector')
        data['market_cap'] = profile.get('mktCap')
        data['current_price'] = profile.get('price')
        data['pe_ratio'] = ratios.get('peRatioTTM')
        data['roe'] = ratios.get('returnOnEquityTTM')
        data['dividend_yield'] = ratios.get('dividendYieldTTM')
        # Add fallback for div yield
        if data['dividend_yield'] is None and data['current_price'] and profile.get(
                'lastDiv'):
            try:
                data['dividend_yield'] = profile['lastDiv'] / \
                    data['current_price']
            except BaseException:
                pass
        data['debt_equity_ratio'] = ratios.get('debtEquityRatioTTM')
        data['revenue_growth'] = growth.get('revenue_growth')
        data['earnings_growth'] = growth.get('earnings_growth')
        # data['ev_ebitda'] = get_ev_ebitda(ticker) # Fetch if needed

        # --- Clean Data ---
        numeric_keys = [
            k for k,
            v in data.items() if k not in [
                'ticker',
                'company_name',
                'sector']]
        for key in numeric_keys:  # Convert to float, handle errors
            val = data.get(key)
            if val is not None:
                try:
                    data[key] = float(val)
                except BaseException:
                    data[key] = None
            else:
                data[key] = None

        return data
    except Exception as e:
        logging.error(f"Failed processing {ticker}: {e}", exc_info=True)
        return None


def update_sqlite_table(all_ticker_data):
    if not all_ticker_data:
        return
    conn = None
    cursor = None
    try:
        conn = get_sqlite_connection()
        ensure_db_table_exists(conn)
        cursor = conn.cursor()
        data_to_upsert = []
        now_str = datetime.now(datetime.timezone.utc).isoformat()

        for data in all_ticker_data:
            if data and data.get('ticker'):
                # Ensure row tuple matches columns list order
                row = tuple(data.get(col) for col in columns[:-1]) + (now_str,)
                data_to_upsert.append(row)

        if not data_to_upsert:
            return

        placeholders = ', '.join(['?'] * len(columns))
        update_cols = ', '.join(
            [f"{col}=excluded.{col}" for col in columns if col != 'ticker'])
        sql = f""" INSERT INTO {DB_TABLE_NAME} ({', '.join(columns)}) VALUES ({
            placeholders})
                    ON CONFLICT(ticker) DO UPDATE SET {update_cols} """

        logging.info(
            f"Executing SQLite UPSERT for {
                len(data_to_upsert)} records...")
        cursor.executemany(sql, data_to_upsert)
        conn.commit()
        logging.info(f"SQLite Update Committed {len(data_to_upsert)} records.")
    except Exception as e:
        logging.error(f"SQLite update failed: {e}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def run_update_process():
    logging.info("--- Starting Manual Data Update Process ---")
    target_tickers = STOCK_UNIVERSE
    if not target_tickers:
        logging.error("STOCK_UNIVERSE is empty. Aborting.")
        return

    processed_data_list = []
    logging.info(f"Processing {len(target_tickers)} tickers...")
    for i, ticker in enumerate(target_tickers):
        processed_data = fetch_and_process_ticker(ticker)
        if processed_data:
            processed_data_list.append(processed_data)
        else:
            logging.warning(f"Skipping {ticker} due to processing failure.")
        logging.debug(f"Sleeping for {API_DELAY_SECONDS}s...")
        time.sleep(API_DELAY_SECONDS)

    logging.info(
        f"Finished fetching. Processed {
            len(processed_data_list)} tickers successfully.")
    update_sqlite_table(processed_data_list)
    logging.info("--- Manual Data Update Process Finished ---")


if __name__ == "__main__":
    print(f"--- Populating SQLite Cache ({SQLITE_DB_PATH}) ---")
    print(f"This will fetch data for {len(STOCK_UNIVERSE)} tickers.")
    print("Running... Check console for progress and logs for errors.")
    run_update_process()
    print("--- Cache Population Complete ---")
