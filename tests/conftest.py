import sqlite3
import pandas as pd
import pytest
from unittest.mock import MagicMock


# Database fixtures
@pytest.fixture()
def db_conn():
    """
    Yield an in-memory SQLite connection with the token_prices schema.

    The connection is closed and discarded after each test.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE token_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            price_gold INTEGER NOT NULL,
            region TEXT NOT NULL,
            ema REAL,
            price_change_abs INTEGER,
            price_change_pct REAL
        )
    """)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    """Return a small but realistic price DataFrame for UI/figure tests."""
    return pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=5, freq="20min"),
            "price_gold": [300_000, 301_000, 299_000, 302_000, 305_000],
            "ema": [300_000.0, 300_250.0, 299_937.5, 300_468.75, 301_484.375],
            "price_change_abs": [0, 1_000, -2_000, 3_000, 3_000],
            "price_change_pct": [0.0, 0.333, -0.664, 1.001, 0.993],
        }
    )


# Cache fixtures
@pytest.fixture()
def mock_cache():
    """Simple in-memory dict-backed mock for Flask-Caching."""
    store: dict = {}
    cache = MagicMock()
    cache.get.side_effect = store.get
    cache.set.side_effect = lambda key, value, **_kw: store.update({key: value})
    return cache
