from datetime import datetime, timezone
from typing import Optional, Tuple
import sqlite3
from sqlite3 import Connection, Cursor
from config import DB_PATH, COPPER_PER_GOLD, EMA_SPAN_DAYS

# Ensure the 'data' directory exists within the project root before initializing the DB.
DB_PATH.parent.mkdir(exist_ok=True)


def get_db_connection() -> Connection:
    """
    Establishes a connection to the SQLite database with a defined timeout.

    Enables Write-Ahead Logging (WAL) mode to improve concurrency and
    performance for mixed read/write operations.

    Returns:
        sqlite3.Connection: The active database connection object.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)

    # Optimize performance and concurrency using WAL mode
    conn.execute("PRAGMA journal_mode=WAL;")

    return conn


def initialize_db() -> None:
    """
    Initializes the SQLite database schema and performs migrations.

    1. Creates the 'token_prices' table if it does not exist.
    2. Checks for new columns and adds them if missing.
    3. Creates a composite index for efficient querying by region and date.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Base Table Creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                price_gold INTEGER NOT NULL,
                region TEXT NOT NULL
            )
        """)

        # Check and add missing columns dynamically
        cursor.execute("PRAGMA table_info(token_prices)")
        existing_columns = [info[1] for info in cursor.fetchall()]

        new_columns = {
            "ema": "INTEGER",
            "price_change_abs": "INTEGER",
            "price_change_pct": "REAL",
        }

        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE token_prices ADD COLUMN {col_name} {col_type}"
                )

        # Optimize sorting by date within a specific region
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_region_date ON token_prices(region, datetime)"
        )

        conn.commit()


def _get_last_record(
    cursor: Cursor, region: str
) -> Optional[Tuple[int, Optional[int]]]:
    """
    Internal helper to fetch the most recent price and EMA for a specific region.

    Args:
        cursor (sqlite3.Cursor): The active database cursor.
        region (str): The region identifier.

    Returns:
        Optional[Tuple[int, Optional[int]]]: A tuple containing (price_gold, ema)
        if a record exists, otherwise None.
    """
    cursor.execute(
        """SELECT price_gold, ema
           FROM token_prices
           WHERE region = ?
           ORDER BY datetime DESC LIMIT 1""",
        (region,),
    )
    return cursor.fetchone()


def save_price(price_copper: int, region: str) -> None:
    """
    Calculates metrics and saves the current WoW Token price to the database.

    1. Converts raw copper value to gold.
    2. Fetches the previous record to calculate price changes.
    3. Calculates the new Exponential Moving Average.
    4. Inserts the fully calculated record with a UTC timestamp.

    Args:
        price_copper (int): The WoW Token price in copper.
        region (str): The region identifier.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            current_gold = price_copper // COPPER_PER_GOLD

            # Retrieve previous data for comparison and EMA calculation
            last_record = _get_last_record(cursor, region)

            if last_record:
                last_price, last_ema = last_record

                # Calculate Price Movement
                change_abs = current_gold - last_price
                change_pct = (change_abs / last_price) * 100

                # EMA Calculation
                # Use previous price as EMA seed if previous EMA is null
                prev_ema = last_ema if last_ema is not None else last_price

                # Smoothing factor based on configured span
                alpha = 2 / (EMA_SPAN_DAYS + 1)
                current_ema = (current_gold * alpha) + (prev_ema * (1 - alpha))

            else:
                # First record for this region; initialize defaults
                change_abs = 0
                change_pct = 0.0
                current_ema = current_gold

            cursor.execute(
                """INSERT INTO token_prices
                (datetime, price_gold, region, ema, price_change_abs, price_change_pct)
                VALUES(?, ?, ?, ?, ?, ?)""",
                (
                    now_utc,
                    current_gold,
                    region,
                    int(current_ema),
                    change_abs,
                    change_pct,
                ),
            )

            conn.commit()

    except Exception as e:
        print(f"ERROR: Failed saving in the database: {e}")
