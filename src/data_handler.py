import pandas as pd
import sqlite3
import os
import time
from config import DB_PATH, CACHE_TIMEOUT_MINUTES, EMPTY_DF_COLUMNS
from data_manager import get_db_connection

def get_db_mtime() -> float:
    """
    Returns the modification time of the SQLite database file.

    This value is used as part of the cache key to force a reload
    whenever the underlying database is updated by the worker.

    Returns:
        The last-modified timestamp, or the current time if the file doesn't exist.
    """
    if DB_PATH.exists():
        return os.path.getmtime(DB_PATH)
    return time.time()


def _load_from_db(region: str) -> pd.DataFrame:
    """
    Queries the database for token prices for the given region.

    Args:
        region: The region identifier.

    Returns:
        A sorted DataFrame with price data, or an empty DataFrame on error.
    """
    if not DB_PATH.exists():
        return pd.DataFrame(columns=EMPTY_DF_COLUMNS)

    try:
        with get_db_connection() as conn:
            sql_query = """
                SELECT datetime, price_gold, ema, price_change_abs, price_change_pct
                FROM token_prices
                WHERE region = ?
                ORDER BY datetime ASC
            """
            df = pd.read_sql_query(sql_query, conn, params=(region,))

        if not df.empty:
            df["datetime"] = pd.to_datetime(df["datetime"])

        return df

    except sqlite3.Error as e:
        print(f"SQLite error during data loading for region '{region}': {e}")
        return pd.DataFrame(columns=EMPTY_DF_COLUMNS)


def load_data(mtime: float, cache, region: str) -> pd.DataFrame:
    """
    Loads and returns WoW token price data for a specific region, using the
    cache to avoid redundant database queries.

    Cache invalidation is driven by 'mtime': when the database file changes,
    the key changes and a fresh query is made.

    Args:
        mtime: Modification time of the database file, used as part of the cache key.
        cache: The Flask-Caching instance.
        region: The region identifier.

    Returns:
        A DataFrame containing price data for the given region.
    """
    cache_key = f"token_data_{region}_{mtime}"
    cached_df = cache.get(cache_key)

    if cached_df is not None:
        return cached_df

    df = _load_from_db(region=region)
    cache.set(cache_key, df, timeout=60 * CACHE_TIMEOUT_MINUTES)
    return df
