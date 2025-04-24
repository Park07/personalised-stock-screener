# data_access.py
import logging
import os
import sqlite3
from .database import get_sqlite_connection
from config import SQLITE_DB_PATH

DB_TABLE_NAME = "stock_metrics_cache"

def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    """Helper to return rows as dictionaries."""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def get_selectable_companies(sector_filter: str = None) -> list[dict]:
    """
    Fetches basic info for all companies in the cache for selection lists.
    Optionally filters by sector.
    """
    if not os.path.exists(SQLITE_DB_PATH):
        logging.warning(f"Database file not found: {SQLITE_DB_PATH}")
        return []

    sql = f"SELECT ticker, company_name, sector FROM {DB_TABLE_NAME}"
    params: list = []
    if sector_filter and sector_filter.lower() != 'all':
        sql += " WHERE LOWER(sector) = LOWER(?)"
        params.append(sector_filter)
    sql += " ORDER BY company_name"

    logging.debug(f"SQL Query (selectable): {sql!r} Params: {params}")

    try:
        conn = get_sqlite_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (DB_TABLE_NAME,)
        )
        if not cursor.fetchone():
            logging.error(f"Table {DB_TABLE_NAME} does not exist.")
            return []

        cursor.execute(sql, params)
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Error in get_selectable_companies: {e}", exc_info=True)
        return []
    finally:
        cursor and cursor.close()
        conn and conn.close()

def get_all_metrics_for_ranking(sector_filter: str = None) -> list[dict]:
    """
    Fetches all stored metrics for ranking computations.
    Optionally filters by sector.
    """
    print(f"get_all_metrics_for_ranking called with sector={sector_filter}")

    if not os.path.exists(SQLITE_DB_PATH):
        logging.error(f"SQLite DB file missing: {SQLITE_DB_PATH}")
        return []

    sql = f"""
        SELECT
            ticker,
            company_name,
            sector,
            market_cap,
            current_price,
            pe_ratio,
            ev_ebitda,
            dividend_yield,
            payout_ratio,
            debt_equity_ratio,
            current_ratio,
            revenue_growth,
            earnings_growth,
            ocf_growth,
            website
        FROM {DB_TABLE_NAME}
        WHERE company_name IS NOT NULL
    """
    params: list = []
    if sector_filter and sector_filter.lower() != 'all':
        sql += " AND LOWER(sector) = LOWER(?)"
        params.append(sector_filter)

    logging.debug(f"SQL Query (ranking): {sql!r} Params: {params}")

    try:
        conn = get_sqlite_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (DB_TABLE_NAME,)
        )
        if not cursor.fetchone():
            logging.error(f"Table {DB_TABLE_NAME} does not exist.")
            return []

        cursor.execute(sql, params)
        results = cursor.fetchall()
        logging.info(f"Fetched {len(results)} records for ranking.")
        return results

    except Exception as e:
        logging.error(f"Error in get_all_metrics_for_ranking: {e}", exc_info=True)
        return []
    finally:
        cursor and cursor.close()
        conn and conn.close()

def get_metrics_for_comparison(ticker_list: list[str]) -> list[dict]:
    """
    Fetches stored metrics for a given list of tickers (for comparison views).
    """
    if not ticker_list or not os.path.exists(SQLITE_DB_PATH):
        return []

    placeholders = ",".join("?" for _ in ticker_list)
    sql = f"SELECT * FROM {DB_TABLE_NAME} WHERE ticker IN ({placeholders})"

    try:
        conn = get_sqlite_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute(sql, ticker_list)
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Error in get_metrics_for_comparison: {e}", exc_info=True)
        return []
    finally:
        cursor and cursor.close()
        conn and conn.close()
