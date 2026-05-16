import logging
import os
import sqlite3
import time
import pandas as pd
import numpy as np

from config import (
    DB_PATH,
    EMPTY_DF_COLUMNS,
    PERCENTILE_WINDOW_DAYS,
    SAMPLING_THRESHOLD_ROWS,
    get_settings,
)
from db_writer import get_db_connection

logger = logging.getLogger(__name__)


# Helpers
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


def maybe_downsample(
    df: pd.DataFrame, threshold: int = SAMPLING_THRESHOLD_ROWS
) -> pd.DataFrame:
    """
    Uniformly downsample *df* to at most *threshold* rows for rendering
    performance. The first and last rows are always preserved.

    Args:
        df: Source DataFrame, assumed to be chronologically sorted.
        threshold: Maximum number of rows to return.

    Returns:
        Downsampled (or original) DataFrame with a reset index.
    """
    if len(df) <= threshold:
        return df

    indices = np.linspace(0, len(df) - 1, threshold, dtype=int)
    return df.iloc[indices].reset_index(drop=True)


# Primary load
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
    """
    cache_key = f"token_data_{region}_{mtime}"
    cached_df: pd.DataFrame | None = cache.get(cache_key)

    if cached_df is not None:
        logger.debug("Cache hit for key '%s'.", cache_key)
        return cached_df

    logger.debug("Cache miss - loading from DB for region '%s'.", region)
    df = _load_from_db(region=region)
    cache.set(cache_key, df, timeout=60 * get_settings().cache_timeout_minutes)
    return df


# Multi-region
def load_data_multi_region(
    mtime: float, cache, regions: list[str]
) -> dict[str, pd.DataFrame]:
    """
    Load data for each region in *regions* and return a mapping of
    region → DataFrame.  Each region's data is cached independently.

    Args:
        mtime: Current DB modification time (used as cache key component).
        cache: Flask-Caching instance.
        regions: List of region identifiers to load.
    """
    return {region: load_data(mtime, cache, region) for region in regions}


# OHLC aggregation
def build_ohlc_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate raw price data into daily OHLC (open / high / low / close) candles.

    Args:
        df: DataFrame with 'datetime' and 'price_gold' columns.

    Returns:
        DataFrame with columns: date, open, high, low, close, volume (row count
        per day). Returns an empty DataFrame with those columns when *df* is empty.
    """
    empty = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    if df.empty:
        return empty

    work = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(work["datetime"]):
        work["datetime"] = pd.to_datetime(work["datetime"])

    work["date"] = work["datetime"].dt.date

    ohlc = (
        work.groupby("date")
        .agg(
            open=("price_gold", "first"),
            high=("price_gold", "max"),
            low=("price_gold", "min"),
            close=("price_gold", "last"),
            volume=("price_gold", "count"),
        )
        .reset_index()
    )
    ohlc["date"] = pd.to_datetime(ohlc["date"])
    return ohlc


# Heatmap aggregation
def build_heatmap_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce a pivot table of the mean token price indexed by UTC day-of-week
    (rows) and hour-of-day (columns), suitable for ``go.Heatmap``.

    Args:
        df: DataFrame with 'datetime' and 'price_gold' columns.

    Returns:
        Pivot DataFrame (day strings x hour integers).  Empty DataFrame if
        *df* contains fewer than 24 rows.
    """
    if df.empty or len(df) < 24:
        return pd.DataFrame()

    work = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(work["datetime"]):
        work["datetime"] = pd.to_datetime(work["datetime"])

    work["hour"] = work["datetime"].dt.hour
    work["day_of_week"] = work["datetime"].dt.day_name()

    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    pivot = (
        work.groupby(["day_of_week", "hour"])["price_gold"]
        .mean()
        .unstack(fill_value=np.nan)
    )
    return pivot.reindex([d for d in day_order if d in pivot.index])


# Percentile
def get_price_percentile(
    current_price: float,
    df: pd.DataFrame,
    window_days: int = PERCENTILE_WINDOW_DAYS,
) -> float | None:
    """
    Return the percentile rank of *current_price* within the price distribution
    over the last *window_days* days.

    A result of 20 means the current price is cheaper than 80 % of historical
    prices in the window — i.e. a good time to buy.

    Args:
        current_price: The latest price in gold.
        df: Full history DataFrame with 'datetime' and 'price_gold' columns.
        window_days: How many days back to look.

    Returns:
        Float percentile [0, 100], or None if there is insufficient data.
    """
    if df.empty or current_price is None:
        return None

    work = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(work["datetime"]):
        work["datetime"] = pd.to_datetime(work["datetime"])

    cutoff = work["datetime"].max() - pd.Timedelta(days=window_days)
    window_df = work[work["datetime"] >= cutoff]

    if len(window_df) < 2:
        return None

    prices = window_df["price_gold"].values
    return round(float(np.mean(prices <= current_price) * 100), 1)
