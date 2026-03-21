from unittest.mock import patch
import pandas as pd
import sqlite3
import src.db_reader


# get_db_mtime
def test_get_db_mtime_returns_float_when_file_exists(tmp_path):
    db = tmp_path / "test.db"
    db.write_bytes(b"")
    with patch.object(src.db_reader, "DB_PATH", db):
        mtime = src.db_reader.get_db_mtime()
    assert isinstance(mtime, float)
    assert mtime > 0


def test_get_db_mtime_returns_current_time_when_missing(tmp_path):
    missing = tmp_path / "no.db"
    with patch.object(src.db_reader, "DB_PATH", missing):
        mtime = src.db_reader.get_db_mtime()
    assert isinstance(mtime, float)


# _load_from_db
def test_load_from_db_returns_empty_df_when_no_file(tmp_path):
    missing = tmp_path / "no.db"
    with patch.object(src.db_reader, "DB_PATH", missing):
        df = src.db_reader._load_from_db("eu")

    assert df.empty
    assert list(df.columns) == src.db_reader.EMPTY_DF_COLUMNS


def test_load_from_db_returns_correct_columns(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("""
        CREATE TABLE token_prices (
            id INTEGER PRIMARY KEY,
            datetime TEXT, price_gold INTEGER, region TEXT,
            ema REAL, price_change_abs INTEGER, price_change_pct REAL
        )
    """)
    conn.execute(
        "INSERT INTO token_prices VALUES (1,'2024-01-01 00:00:00',300000,'eu',300000.0,0,0.0)"
    )
    conn.commit()
    conn.close()

    with patch.object(src.db_reader, "DB_PATH", db):
        df = src.db_reader._load_from_db("eu")

    assert not df.empty
    assert "datetime" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["datetime"])


def test_load_from_db_filters_by_region(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("""
        CREATE TABLE token_prices (
            id INTEGER PRIMARY KEY,
            datetime TEXT, price_gold INTEGER, region TEXT,
            ema REAL, price_change_abs INTEGER, price_change_pct REAL
        )
    """)
    conn.execute(
        "INSERT INTO token_prices VALUES (1,'2024-01-01',300000,'eu',300000.0,0,0.0)"
    )
    conn.execute(
        "INSERT INTO token_prices VALUES (2,'2024-01-01',320000,'us',320000.0,0,0.0)"
    )
    conn.commit()
    conn.close()

    _orig_connect = sqlite3.connect
    with patch.object(src.db_reader, "DB_PATH", db), patch.object(sqlite3, "connect", side_effect=lambda *_args, **kw: _orig_connect(str(db), **kw)):
        df_eu = src.db_reader._load_from_db("eu")
        df_us = src.db_reader._load_from_db("us")

    assert len(df_eu) == 1
    assert len(df_us) == 1


# load_data — cache behaviour
def test_load_data_cache_miss_calls_db(mock_cache, sample_df, tmp_path):
    missing = tmp_path / "no.db"
    with patch.object(src.db_reader, "DB_PATH", missing):
        df = src.db_reader.load_data(mtime=1.0, cache=mock_cache, region="eu")

    mock_cache.set.assert_called_once()
    assert isinstance(df, pd.DataFrame)


def test_load_data_cache_hit_skips_db(mock_cache, sample_df):
    mock_cache.get.side_effect = lambda key: sample_df

    with patch("db_reader._load_from_db") as mock_load:
        df = src.db_reader.load_data(mtime=1.0, cache=mock_cache, region="eu")

    mock_load.assert_not_called()
    assert len(df) == len(sample_df)


def test_load_data_cache_key_includes_region_and_mtime(mock_cache, tmp_path):
    missing = tmp_path / "no.db"
    with patch.object(src.db_reader, "DB_PATH", missing):
        src.db_reader.load_data(mtime=42.5, cache=mock_cache, region="kr")

    key_used = mock_cache.set.call_args[0][0]
    assert "kr" in key_used
    assert "42.5" in key_used
