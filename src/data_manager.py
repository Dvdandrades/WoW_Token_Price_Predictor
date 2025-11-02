from datetime import datetime, timezone
from pathlib import Path
import sqlite3

# Define the project root directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define the full path for the SQLite database file where WoW Token price data will be stored.
# The path is set to "<project_root>/data/wow_token_prices.db".
DB_PATH = PROJECT_ROOT / "data" / "wow_token_prices.db"

# Ensure the 'data' directory exists within the project root before attempting to create the database file.
DB_PATH.parent.mkdir(exist_ok=True)


def initialize_db():
    """
    Initializes the SQLite database and creates the 'token_prices' table
    if it does not already exist.
    The table stores the timestamp and the WoW Token price in gold.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            price_gold INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_price(price_cooper):
    """
    Saves the WoW Token price to the SQLite database.
    
    The input price is assumed to be in cooper (1 gold = 10,000 cooper).
    It converts the price to gold and stores it with the current UTC timestamp.
    
    Args:
        price_cooper (int): The WoW Token price in cooper coins.
    """
    conn = sqlite3.connect(DB_PATH)

    try:
        # Get the current time in UTC and format it for database storage
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert the price from cooper to gold (10,000 cooper = 1 gold)
        gold = price_cooper // 10000

        # Insert the data into the 'token_prices' table
        cursor = conn.cursor()
        cursor.execute("INSERT INTO token_prices (datetime, price_gold) VALUES (?, ?)", (now_utc, gold))
        conn.commit()
        
        print(f"[{now_utc} UTC] WoW Token price successfully saved to SQLite: {gold} gold.")

    except Exception as e:
        # Detailed error message for any failure during the save operation
        print(f"**ERROR:** Failed to save price data to the database. Details: {e}")

    finally:
        # Ensure the database connection is always closed
        conn.close()