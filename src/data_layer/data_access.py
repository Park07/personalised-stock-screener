# data_access.py
import logging
import sqlite3
import os
from .database import get_sqlite_connection
from config import SQLITE_DB_PATH

DB_TABLE_NAME = "stock_metrics_cache"

def dict_factory(cursor, row):
    # Helper to return rows as dictionaries
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def get_selectable_companies(sector_filter=None):
    """Fetches basic info for all companies in the cache for selection lists."""
    # Initialise results outside the try block
    results = []
    
    # Check if database exists
    if not os.path.exists(SQLITE_DB_PATH):
        logging.warning(f"Database file not found: {SQLITE_DB_PATH}")
        return []
        
    conn = None
    cursor = None
    params = []
    
    # Basic query - one clause at a time to avoid syntax errors
    sql = f"SELECT ticker, company_name, sector FROM {DB_TABLE_NAME}"
    
    # Only add WHERE if we have a sector filter
    if sector_filter and sector_filter.lower() != 'all':
        sql += " WHERE LOWER(sector) = LOWER(?)"
        params.append(sector_filter)
    
    # Add the ORDER BY clause (only once)
    sql += " ORDER BY company_name"
    
    # Log the exact SQL and parameters for debugging
    logging.info(f"SQL Query: {sql}")
    logging.info(f"SQL Params: {params}")
    
    try:
        conn = get_sqlite_connection()
        
        # Check if the table exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{DB_TABLE_NAME}'")
        if not cursor.fetchone():
            logging.error(f"Table {DB_TABLE_NAME} does not exist in the database")
            return []
            
        # Set row factory for dictionary results
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(sql, params)
        results = cursor.fetchall()
        logging.info(f"Query returned {len(results)} results")
        
    except Exception as e:
        logging.error(f"Error querying selectable companies: {e}")
        # For debugging, include the full exception trace
        logging.error(f"Exception traceback: {traceback.format_exc()}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
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