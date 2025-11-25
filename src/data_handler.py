import pandas as pd
import sqlite3
import os
import time
from config import DB_PATH, CACHE_TIMEOUT_MINUTES
from data_manager import get_db_connection


def get_db_mtime() -> float:
    """
    Returns the modification time of the SQLite database file.

    This time is used as a cache key to force a cache reload whenever the
    underlying database file is updated by the worker.

    Returns:
        float: The time of the last modification,
               or the current time if the file does not exist.
    """
    # Check if the database file exists
    if DB_PATH.exists():
        # Return the time of the last modification
        return os.path.getmtime(DB_PATH)
    # If the database file is not found, return the current time
    return time.time()


def load_data(mtime: float, cache, region: str) -> pd.DataFrame:
    """
    Load and preprocess the WoW token price data for a specific region from
    the SQLite database, utilizing a cache.

    The 'mtime' parameter forces cache invalidation when the underlying database file changes.

    Parameters
    ----------
    mtime : float
        Modification time of the database file used as the cache key.
    cache : dash.caching.Cache
        The Dash application's cache object.
    region: str
        The region for which the data is being loaded.

    Returns
    -------
    pandas.DataFrame
        A sorted DataFrame containing 'datetime', 'price_gold', and
        derived metrics.
    """

    # Decorator to cache the result of the function call based on its arguments.
    # If the DB file changes, 'mtime' changes, and the cache is invalidated.
    @cache.memoize(timeout=60 * CACHE_TIMEOUT_MINUTES)
    def cached_load(mtime, region):
        # Check if the database file exists before attempting connection.
        if not DB_PATH.exists():
            # Return an empty DataFrame with expected columns if the DB is missing
            return pd.DataFrame(
                columns=[
                    "datetime",
                    "price_gold",
                    "ema",
                    "price_change_abs",
                    "price_change_pct",
                ]
            )

        try:
            # Connect to the SQLite database
            with get_db_connection() as conn:
                # Select all required columns for the specific region, ordered by time
                sql_query = "SELECT datetime, price_gold, ema, price_change_abs, price_change_pct FROM token_prices WHERE region = ? ORDER BY datetime ASC"
                df = pd.read_sql_query(sql_query, conn, params=(region,))

            if df.empty:
                return df

            # Convert the 'datetime' column to the proper pandas datetime type
            df["datetime"] = pd.to_datetime(df["datetime"])

            return df

        except sqlite3.Error as e:
            # Handle potential SQLite errors during connection or query execution
            print(f"SQLite Error during data loading: {e}")
            # Return an empty DataFrame with the expected columns in case of error
            return pd.DataFrame()

    # Call the decorated function with the modification time to trigger caching
    return cached_load(mtime, region)
