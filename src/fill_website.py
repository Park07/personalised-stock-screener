#!/usr/bin/env python3
import sqlite3
import requests
import time
import logging
from config import SQLITE_DB_PATH  # ← our single source-of-truth

CLEARBIT_AUTOCOMPLETE = "https://autocomplete.clearbit.com/v1/companies/suggest"
DB = SQLITE_DB_PATH

EXCEPTIONS = {
    'BK': 'bnymellon.com',
    'C':  'citigroup.com',
}

def get_domain(company_name: str) -> str | None:
    try:
        resp = requests.get(
            CLEARBIT_AUTOCOMPLETE,
            params={"query": company_name},
            timeout=5
        )
        resp.raise_for_status()
        suggestions = resp.json()
        if suggestions:
            return suggestions[0].get("domain")
    except Exception as e:
        logging.warning(f"Clearbit lookup failed for {company_name!r}: {e}")
    return None

def main():
    # 1) Make sure your table has a `website` column
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    # This will add the column if it doesn’t exist yet:
    cur.execute("""
      PRAGMA table_info(stock_metrics_cache)
    """)
    cols = [r[1] for r in cur.fetchall()]
    if "website" not in cols:
        cur.execute("""
          ALTER TABLE stock_metrics_cache
            ADD COLUMN website TEXT
        """)
        conn.commit()

    # 2) Fetch every row and back-fill
    cur.execute("SELECT ticker, company_name FROM stock_metrics_cache")
    rows = cur.fetchall()

    for ticker, name in rows:
        domain = EXCEPTIONS.get(ticker) or get_domain(name or ticker)
        if domain:
            website = f"https://{domain}"
            cur.execute(
              "UPDATE stock_metrics_cache SET website = ? WHERE ticker = ?",
              (website, ticker)
            )
            print(f"{ticker} → {domain}")
        else:
            print(f"{ticker} → <no suggestion>")
        conn.commit()
        time.sleep(0.2)   # throttle for rate-limit safety

    cur.close()
    conn.close()
    print("Done back-filling websites.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
