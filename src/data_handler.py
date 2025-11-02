# data_handler.py
import pandas as pd
import time
import sqlite3
import os
from data_manager import DB_PATH

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
    @cache.memoize(timeout=60 * 5)  # Cache data for 5 minutes
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

            # Data Preprocessing: Convert 'datetime' to timezone-naive datetime objects
            # and 'price_gold' to integer type.
            df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize(None)
            df["price_gold"] = df["price_gold"].astype(int)
            return df
        except sqlite3.Error as e:
            print(f"SQLite Error during data loading: {e}")
            return pd.DataFrame(columns=["datetime", "price_gold"])
    
    return cached_load(mtime)