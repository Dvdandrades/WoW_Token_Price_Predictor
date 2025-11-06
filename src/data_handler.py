import pandas as pd
import time
import sqlite3
import os
from config import DB_PATH, EMA_SPAN_DAYS, CACHE_TIMEOUT_MINUTES

def get_db_mtime():
    """Returns the modification time of the SQLite database file, or current time if it doesn't exist."""
    if DB_PATH.exists():
        return os.path.getmtime(DB_PATH)
    return time.time()


def load_data(mtime, cache):
    """
    Load and preprocess the WoW token price data from the SQLite database, utilizing a cache.

    The 'mtime' parameter forces cache invalidation when the underlying database file changes.

    Parameters
    ----------
    mtime : float
        Modification time of the database file used as the cache key.
    cache : dash.caching.Cache
        The Dash application's cache object.

    Returns
    -------
    pandas.DataFrame
        A sorted DataFrame containing 'datetime' (tz-naive) and 'price_gold' columns.
    """
    @cache.memoize(timeout=60 * CACHE_TIMEOUT_MINUTES)  # Cache data for 19 minutes
    def cached_load(mtime):
        # Check if the database file exists before attempting connection.
        if not DB_PATH.exists():
            print(f"Database not found at {DB_PATH}. Returning empty DataFrame.")
            return pd.DataFrame(columns=["datetime", "price_gold"])

        try:
            # Connect to the SQLite database and read all data into a DataFrame.
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query(
                "SELECT datetime, price_gold FROM token_prices ORDER BY datetime",
                conn
            )
            conn.close()

            # Data Preprocessing: Convert 'datetime' to timezone-naive datetime objects and 'price_gold' to integer type
            df["datetime"] = pd.to_datetime(df["datetime"])
            df["price_gold"] = df["price_gold"].astype(int)

            # Calculate the absolute difference and the percentage change between consecutive prices.
            df["price_change_abs"] = df["price_gold"].diff()
            df["price_change_pct"] = df["price_gold"].pct_change() * 100

            # Compute the 7-day Exponential Moving Average.
            df["ema"] = df["price_gold"].ewm(span=EMA_SPAN_DAYS, adjust=False).mean().round().astype('Int64')
            return df
        except sqlite3.Error as e:
            print(f"SQLite Error during data loading: {e}")
            return pd.DataFrame(columns=["datetime", "price_gold", "ema"])
    
    return cached_load(mtime)