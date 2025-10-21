import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# Define the path to the CSV file where WoW Token price data will be stored.
# The path is set to "<project_root>/data/wow_token_prices.csv".
DATA_PATH = Path(__file__).parent.parent / "data" / "wow_token_prices.csv"

# Ensure the "data" directory exists before writing files.
DATA_PATH.parent.mkdir(exist_ok=True)

def save_price(price_cooper):
    """
    Save the current WoW Token price to a CSV file.

    This function records the current datetime (in UTC) and the token price converted to gold. 
    The data is appended to an existing CSV file if it exists, or a new one is created otherwise.

    Args:
        price_cooper (int): The token price in copper units (1 gold = 10,000 copper).

    Example:
        save_price(3500000)  # Saves 350 gold at the current UTC time.
    """
    # Get the current time in UTC and format it as an ISO 8601 string.
    now = datetime.now(timezone.utc).isoformat()

    # Convert copper to gold (integer division).
    gold = price_cooper // 10000

    # Create a single-row DataFrame with the timestamp and prices.
    df = pd.DataFrame([{"datetime": now, "price_gold": gold}])

    # If the CSV file already exists, append without headers.
    # Otherwise, create a new CSV with headers.
    if DATA_PATH.exists():
        df.to_csv(DATA_PATH, mode='a', header=False, index=False)
    else:
        df.to_csv(DATA_PATH, index=False)

    # Log the save operation to the console.
    print(f"Saved WoW Token price: {gold} gold at {now} in {DATA_PATH}")


def load_data():
    """
    Load all saved WoW Token price data from the CSV file.

    Reads the CSV into a pandas DataFrame, parsing the datetime column,
    and returns the data sorted by time in ascending order.

    Returns:
        pandas.DataFrame: DataFrame containing the WoW Token prices with columns:
            - datetime (datetime64)
            - price_gold (int)

    Raises:
        FileNotFoundError: If the data file does not exist.
    """
    # Check if the CSV file exists before attempting to read.
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"No data file found at {DATA_PATH}")

    # Read the CSV file, parsing the datetime column.
    df = pd.read_csv(DATA_PATH, parse_dates=["datetime"])

    # Return the DataFrame sorted by datetime (oldest first).
    return df.sort_values("datetime")
