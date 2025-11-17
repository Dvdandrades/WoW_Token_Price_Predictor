from datetime import datetime, timezone
from config import DB_PATH
from config import COOPER_PER_GOLD
import sqlite3

# Ensure the 'data' directory exists within the project root before attempting to create the database file.
DB_PATH.parent.mkdir(exist_ok=True)


def initialize_db():
    """
    Initializes the SQLite database and creates the 'token_prices' table
    if it does not already exist.
    The table stores the timestamp and the WoW Token price in gold.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                price_gold INTEGER NOT NULL
            )
        """)
        conn.commit()


def save_price(price_cooper: int):
    """
    Saves the WoW Token price to the SQLite database.

    The input price is assumed to be in cooper (1 gold = 10,000 cooper).
    It converts the price to gold and stores it with the current UTC timestamp.

    Args:
        price_cooper (int): The WoW Token price in cooper coins.
    """

    try:
        # Connect to the SQLite database
        with sqlite3.connect(DB_PATH) as conn:
            # Get the current time in UTC and format it for database storage
            now_utc: str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # Convert the price from cooper to gold (10,000 cooper = 1 gold)
            gold: int = price_cooper // COOPER_PER_GOLD

            # Insert the data into the 'token_prices' table
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO token_prices (datetime, price_gold) VALUES (?, ?)",
                (now_utc, gold),
            )
            conn.commit()

            print(
                f"[{now_utc} UTC] WoW Token price successfully saved to SQLite: {gold} gold."
            )

    except Exception as e:
        # Detailed error message for any failure during the save operation
        print(f"**ERROR:** Failed to save price data to the database. Details: {e}")
