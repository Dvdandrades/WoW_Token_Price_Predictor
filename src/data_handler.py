import pandas as pd
import time
import sqlite3
import os
from config import DB_PATH, EMA_SPAN_DAYS, CACHE_TIMEOUT_MINUTES


def get_db_mtime() -> float:
    """Returns the modification time of the SQLite database file, or current time if it doesn't exist."""
    # Check if the database file exists
    if DB_PATH.exists():
        # Return the time of the last modification
        return os.path.getmtime(DB_PATH)
    # If the database file is not found, return the current time (used to force cache update if DB appears)
    return time.time()


def _preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies data type conversions, calculates price changes (absolute and percentage),
    and computes the Exponential Moving Average (EMA).

    Parameters
    ----------
    df : pandas.DataFrame
        The raw DataFrame loaded from the database.

    Returns
    -------
    pandas.DataFrame
        The processed DataFrame with additional calculated columns.
    """
    if df.empty:
        return df

    # Convert the 'datetime' column to proper datetime objects (tz-naive)
    df["datetime"] = pd.to_datetime(df["datetime"])
    # Convert 'price_gold' to integer type
    df["price_gold"] = df["price_gold"].astype(int)

    # Calculate the absolute difference in price between consecutive rows
    df["price_change_abs"] = df["price_gold"].diff()
    # Calculate the percentage change in price between consecutive rows, multiplied by 100
    df["price_change_pct"] = df["price_gold"].pct_change() * 100

    # Calculate the Exponential Moving Average (EMA) of 'price_gold'
    # 'span' is defined by EMA_SPAN_DAYS, 'adjust=False' uses the legacy weighting formula
    # The result is rounded and converted to an Int64 (integer with support for NaN)
    df["ema"] = (
        df["price_gold"]
        .ewm(span=EMA_SPAN_DAYS, adjust=False)
        .mean()
        .round()
        .astype("Int64")
    )

    return df


def load_data(mtime: float, cache, region: str) -> pd.DataFrame:
    """
    Load and preprocess the WoW token price data and region from the SQLite database, utilizing a cache.

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
        A sorted DataFrame containing 'datetime' (tz-naive) and 'price_gold' columns, plus derived metrics.
    """

    # Decorator to cache the result of the function call based on its arguments.
    # The 'mtime' parameter acts as a cache key: if it changes (DB updated), the cache is invalidated.
    @cache.memoize(timeout=60 * CACHE_TIMEOUT_MINUTES)  # Cache data for 19 minutes
    def cached_load(mtime, region):
        # Check if the database file exists before attempting connection.
        if not DB_PATH.exists():
            print(f"Database not found at {DB_PATH}. Returning empty DataFrame.")
            return pd.DataFrame(columns=["datetime", "price_gold"])

        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(DB_PATH)
            # Read all 'datetime' and 'price_gold' data, ordered by datetime, into a DataFrame
            sql_query = "SELECT datetime, price_gold FROM token_prices WHERE region = ? ORDER BY datetime"
            df = pd.read_sql_query(sql_query, conn, params=(region,))
            # Close the database connection
            conn.close()

            # Apply preprocessing steps to the loaded data
            return _preprocess_data(df)

        except sqlite3.Error as e:
            # Handle potential SQLite errors during connection or query execution
            print(f"SQLite Error during data loading: {e}")
            # Return an empty DataFrame with the expected columns in case of error
            return pd.DataFrame(columns=["datetime", "price_gold", "ema"])

    # Call the decorated function with the modification time to trigger caching
    return cached_load(mtime, region)
