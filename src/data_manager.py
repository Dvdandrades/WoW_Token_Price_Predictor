from datetime import datetime, timezone
from config import DB_PATH, COPPER_PER_GOLD
import sqlite3

# Ensure the 'data' directory exists within the project root before initializing the DB.
DB_PATH.parent.mkdir(exist_ok=True)


def get_db_connection():
    """
    Establishes a connection to the SQLite database with a timeout.
    Enables Write-Ahead Logging (WAL) to handle concurrent reads/writes better.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    
    # optimize performance and concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    
    return conn


def initialize_db():
    """
    Initializes the SQLite database schema.
    
    Creates the 'token_prices' table and a composite index for efficient 
    querying by region and date if they do not already exist.
    """
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

        # Create an index to speed up queries filtering by region and sorting by date
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_region_date ON token_prices(region, datetime)"
        )

        conn.commit()


def save_price(price_copper: int, region: str):
    """
    Saves the WoW Token price and region to the SQLite database.

    The input price is assumed to be in copper. This function converts 
    the price to gold and stores it with the current UTC timestamp.

    Args:
        price_copper (int): The WoW Token price in copper coins.
        region (str): The region for which the price is being saved.
    """
    try:
        with get_db_connection() as conn:
            # Generate current UTC timestamp string
            now_utc: str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # Convert copper to gold
            gold: int = price_copper // COPPER_PER_GOLD

            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO token_prices (datetime, price_gold, region) VALUES (?, ?, ?)",
                (now_utc, gold, region),
            )
            conn.commit()

            print(
                f"[{now_utc} UTC] WoW Token price successfully saved to SQLite: {gold} gold."
            )

    except Exception as e:
        print(f"**ERROR:** Failed to save price data to the database. Details: {e}")