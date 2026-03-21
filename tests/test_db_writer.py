import sqlite3
from contextlib import contextmanager
from unittest.mock import patch
import pytest
import src.db_writer
from src.db_writer import _get_last_record, save_price


# Helpers
def _in_memory_conn():
    """Return a fresh in-memory connection with the token_prices schema."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE token_prices (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime         TEXT    NOT NULL,
            price_gold       INTEGER NOT NULL,
            region           TEXT    NOT NULL,
            ema              REAL,
            price_change_abs INTEGER,
            price_change_pct REAL
        )
    """)
    conn.commit()
    return conn


@contextmanager
def _patch_connection(conn):
    """Context manager that replaces get_db_connection with *conn*."""

    @contextmanager
    def _fake_conn():
        yield conn
        conn.commit()

    with patch.object(src.db_writer, "get_db_connection", _fake_conn):
        yield


# _get_last_record
def test_get_last_record_returns_none_for_empty_table():
    conn = _in_memory_conn()
    cursor = conn.cursor()
    assert _get_last_record(cursor, "eu") is None


def test_get_last_record_returns_most_recent_row():
    conn = _in_memory_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO token_prices (datetime, price_gold, region, ema) VALUES (?, ?, ?, ?)",
        ("2024-01-01 00:00:00", 300_000, "eu", 300_000.0),
    )
    cursor.execute(
        "INSERT INTO token_prices (datetime, price_gold, region, ema) VALUES (?, ?, ?, ?)",
        ("2024-01-01 00:20:00", 305_000, "eu", 302_500.0),
    )
    conn.commit()

    result = _get_last_record(cursor, "eu")
    assert result == (305_000, 302_500.0)


# save_price — first record
def test_save_price_first_record_initialises_change_to_zero():
    conn = _in_memory_conn()
    with _patch_connection(conn):
        save_price(3_000_000_000, "eu")

    row = conn.execute(
        "SELECT price_gold, price_change_abs, price_change_pct FROM token_prices"
    ).fetchone()
    assert row[0] == 300_000  # copper → gold
    assert row[1] == 0  # no previous record
    assert row[2] == pytest.approx(0.0)


def test_save_price_first_record_ema_equals_price():
    conn = _in_memory_conn()
    with _patch_connection(conn):
        save_price(3_000_000_000, "eu")

    row = conn.execute("SELECT price_gold, ema FROM token_prices").fetchone()
    assert row[1] == pytest.approx(row[0])


# save_price — subsequent record
def test_save_price_calculates_positive_change():
    conn = _in_memory_conn()
    with _patch_connection(conn):
        save_price(3_000_000_000, "eu")  # 300_000 gold
        save_price(3_010_000_000, "eu")  # 301_000 gold

    rows = conn.execute(
        "SELECT price_gold, price_change_abs, price_change_pct FROM token_prices ORDER BY id"
    ).fetchall()
    assert rows[1][1] == 1_000  # abs change
    assert rows[1][2] == pytest.approx(1_000 / 300_000 * 100)


def test_save_price_calculates_negative_change():
    conn = _in_memory_conn()
    with _patch_connection(conn):
        save_price(3_000_000_000, "eu")
        save_price(2_990_000_000, "eu")  # price drops

    rows = conn.execute(
        "SELECT price_change_abs FROM token_prices ORDER BY id"
    ).fetchall()
    assert rows[1][0] == -1_000


def test_save_price_ema_is_stored_as_float():
    """EMA must be stored as REAL (not truncated to int)."""
    conn = _in_memory_conn()
    with _patch_connection(conn):
        save_price(3_000_000_000, "eu")
        save_price(3_010_000_000, "eu")

    ema = conn.execute(
        "SELECT ema FROM token_prices ORDER BY id DESC LIMIT 1"
    ).fetchone()[0]
    # The value should not be an exact integer (unless by coincidence)
    assert isinstance(ema, float)


def test_save_price_does_not_raise_on_db_error(caplog):
    """A database error should be caught and logged, not propagated."""
    with patch.object(
        src.db_writer, "get_db_connection", side_effect=sqlite3.Error("boom")
    ):
        save_price(1_000_000, "eu")  # must not raise

    assert any("Failed to save" in r.message for r in caplog.records)


# Region isolation
def test_save_price_stores_correct_region():
    conn = _in_memory_conn()
    with _patch_connection(conn):
        save_price(3_000_000_000, "eu")
        save_price(3_000_000_000, "us")

    regions = {
        row[0] for row in conn.execute("SELECT region FROM token_prices").fetchall()
    }
    assert regions == {"eu", "us"}
