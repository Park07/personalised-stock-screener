# data_access.py
import logging
import sqlite3
import os
from database import get_sqlite_connection
from config import SQLITE_DB_PATH

DB_TABLE_NAME = "stock_metrics_cache"

def dict_factory(cursor, row):
    # Helper to return rows as dictionaries
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def get_selectable_companies():
    """Fetches basic info for all companies in the cache for selection lists."""
    if not os.path.exists(SQLITE_DB_PATH): return []
    conn = None
    cursor = None
    results = []
    sql = f"SELECT ticker, company_name, sector FROM {DB_TABLE_NAME} ORDER BY company_name"
    try:
        conn = get_sqlite_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
    except Exception as e: logging.error(f"Error querying selectable companies: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return results

def get_metrics_for_comparison(ticker_list):
    """Fetches stored metrics from SQLite for parallel chart data."""
    if not ticker_list or not os.path.exists(SQLITE_DB_PATH): return []
    conn = None
    cursor = None
    results = []
    # Select ALL columns stored in the cache table for the specified tickers
    sql = f"SELECT * FROM {DB_TABLE_NAME} WHERE ticker IN ({','.join('?'*len(ticker_list))})"
    try:
        conn = get_sqlite_connection()
        conn.row_factory = dict_factory # Get rows as dicts
        cursor = conn.cursor()
        cursor.execute(sql, ticker_list)
        results = cursor.fetchall() # List of dictionaries
    except Exception as e: logging.error(f"Error querying SQLite for comparison: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    return results # Return list of dicts (raw row data)