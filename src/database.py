import sqlite3 
import logging
import os
from config import DB_CONFIG_RDS, SQLITE_DB_PATH

def get_sqlite_connection():
    """Establishes connection to the local SQLite cache file."""
    conn = None
    try:
        db_dir = os.path.dirname(SQLITE_DB_PATH)
        os.makedirs(db_dir, exist_ok=True) # Create ./data/ directory if needed
        conn = sqlite3.connect(SQLITE_DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row # Access columns by name
        return conn
    except Exception as e:
        logging.error(f"SQLite connection error: {e}")
        raise ConnectionError("Failed to connect to SQLite cache.") from e