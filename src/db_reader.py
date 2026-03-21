import logging
import os
import sqlite3
import time
import pandas as pd

from config import DB_PATH, EMPTY_DF_COLUMNS, settings
from db_writer import get_db_connection

logger = logging.getLogger(__name__)


def get_db_mtime() -> float:
    """
    Return the last-modified timestamp of the SQLite database file.

    Used as part of the cache key so that a fresh mtime forces a cache miss
    and triggers a new database query.

    Returns:
        Modification timestamp, or the current time if the file does not exist.
    """
    if DB_PATH.exists():
        return os.path.getmtime(DB_PATH)
    return time.time()


def _load_from_db(region: str) -> pd.DataFrame:
    """
    Query all token prices for *region* sorted chronologically.

    Returns an empty DataFrame with the expected columns on any error so
    that callers never receive an unexpected schema.

    Args:
        region: Region identifier (e.g. "eu", "us").

    Returns:
        DataFrame with columns defined by EMPTY_DF_COLUMNS.
    """
    if not DB_PATH.exists():
        logger.warning("Database file not found at %s.", DB_PATH)
        return pd.DataFrame(columns=EMPTY_DF_COLUMNS)

    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(
                """
                SELECT datetime, price_gold, ema, price_change_abs, price_change_pct
                FROM token_prices
                WHERE region = ?
                ORDER BY datetime ASC
                """,
                conn,
                params=(region,),
            )

        if not df.empty:
            df["datetime"] = pd.to_datetime(df["datetime"])

        return df

    except sqlite3.Error:
        logger.exception("SQLite error loading data for region '%s'.", region)
        return pd.DataFrame(columns=EMPTY_DF_COLUMNS)


def load_data(mtime: float, cache, region: str) -> pd.DataFrame:
    """
    Return token price data for *region*, using *cache* to avoid redundant
    database queries between dashboard refresh ticks.

    The cache key embeds both the region and the database mtime so that:
    - Different regions are stored independently.
    - Any write by the worker automatically invalidates the cached data.

    Args:
        mtime: Current modification time of the database file.
        cache: Flask-Caching instance.
        region: Region identifier.

    Returns:
        DataFrame with columns defined by EMPTY_DF_COLUMNS.
    """
    cache_key = f"token_data_{region}_{mtime}"
    cached_df: pd.DataFrame | None = cache.get(cache_key)

    if cached_df is not None:
        logger.debug("Cache hit for key '%s'.", cache_key)
        return cached_df

    logger.debug("Cache miss - loading from DB for region '%s'.", region)
    df = _load_from_db(region=region)
    cache.set(cache_key, df, timeout=60 * settings.cache_timeout_minutes)
    return df
