import logging
import sqlite3

from contextlib import contextmanager
from datetime import datetime, timezone
from sqlite3 import Connection, Cursor
from typing import Generator

from config import DB_PATH, COPPER_PER_GOLD, get_settings, VALID_REGIONS


logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """
    Context manager that yields an open SQLite connection with WAL mode
    enabled, then commits on clean exit and always closes the connection.

    Raises:
        sqlite3.Error: Re-raised after rollback on any database error.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    try:
        yield conn
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_db() -> None:
    """
    Create the token_prices table and indexes if they do not exist, and
    add any columns introduced in later schema versions.

    Safe to call on every startup — all operations are idempotent.
    """
    # Ensure the data directory exists before any DB operation.
    DB_PATH.parent.mkdir(exist_ok=True)
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                price_gold INTEGER NOT NULL,
                region TEXT NOT NULL
            )
        """)

        # Schema evolution: add derived-metric columns when missing.
        cursor.execute("PRAGMA table_info(token_prices)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        migrations: dict[str, str] = {
            "ema": "REAL",
            "price_change_abs": "INTEGER",
            "price_change_pct": "REAL",
        }
        for col_name, col_type in migrations.items():
            if col_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE token_prices ADD COLUMN {col_name} {col_type}"
                )
                logger.info(
                    "Schema migration: added column '%s %s'.", col_name, col_type
                )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_region_date ON token_prices(region, datetime)"
        )

    logger.info("Database initialised at %s.", DB_PATH)


def _get_last_record(cursor: Cursor, region: str) -> tuple[int, float | None] | None:
    """Return the most recent (price_gold, ema) for *region*, or None."""
    cursor.execute(
        """
        SELECT price_gold, ema
        FROM token_prices
        WHERE region = ?
        ORDER BY datetime DESC 
        LIMIT 1
        """,
        (region,),
    )
    return cursor.fetchone()


def save_price(price_copper: int, region: str) -> None:
    """
    Convert *price_copper* to gold, compute derived metrics, and insert a
    new row for *region* with a UTC timestamp.

    The EMA is stored as REAL to preserve the float precision of the
    exponential calculation.

    Args:
        price_copper: Raw copper value from the Blizzard API.
        region: Region identifier (e.g. "eu", "us").
    """

    if region not in VALID_REGIONS:
        logger.error("save_price called with unknown region '%s'. Aborting.", region)
        return
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            current_gold = price_copper // COPPER_PER_GOLD

            MIN_GAP_MINUTES = get_settings().worker_interval_minutes // 2
            last_record = _get_last_record(cursor, region)

            if last_record:
                cursor.execute(
                    "SELECT MAX(datetime) FROM token_prices WHERE region=?", (region,)
                )
                last_dt_str = cursor.fetchone()[0]
                if last_dt_str:
                    last_dt = datetime.fromisoformat(last_dt_str).replace(
                        tzinfo=timezone.utc
                    )
                    if (
                        datetime.now(timezone.utc) - last_dt
                    ).seconds < MIN_GAP_MINUTES * 60:
                        logger.info("Too soon for %s, skipping.", region)
                        return

                last_price, last_ema = last_record
                change_abs = current_gold - last_price
                change_pct = (change_abs / last_price) * 100

                prev_ema = last_ema if last_ema is not None else float(last_price)
                alpha = 2.0 / (get_settings().ema_span_days + 1)
                current_ema = (current_gold * alpha) + (prev_ema * (1.0 - alpha))
            else:
                change_abs = 0
                change_pct = 0.0
                current_ema = float(current_gold)

            cursor.execute(
                """
                INSERT INTO token_prices
                    (datetime, price_gold, region, ema, price_change_abs, price_change_pct)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    now_utc,
                    current_gold,
                    region,
                    current_ema,
                    change_abs,
                    change_pct,
                ),
            )

    except (sqlite3.Error, ValueError):
        logger.exception("Failed to save price for region '%s'.", region)
