from api_client import BlizzardAPIClient
from data_manager import save_price, initialize_db
from app import app
from dotenv import load_dotenv
from pathlib import Path

import time
import schedule
import threading
import requests
import os

# Initialization and Configuration Setup
# Define the project root directory relative to this file's location.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Load environment variables (CLIENT_ID, CLIENT_SECRET) from the .env file located at the project's root.
load_dotenv(PROJECT_ROOT / ".env")

# Retrieve Blizzard API credentials and configuration from environment variables.
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# Get the region; defaults to 'eu' if the environment variable is not set.
REGION = os.getenv("REGION", "eu")  
# Set the locale for API responses.
LOCALE = "en_US"
# Define the path for the file used to cache the access token.
TOKEN_CACHE_FILE = PROJECT_ROOT / "data" / "token_cache.json"

try:
    # Initialize the Blizzard API Client with credentials and regional settings.
    api_client = BlizzardAPIClient(CLIENT_ID, CLIENT_SECRET, REGION, LOCALE, TOKEN_CACHE_FILE)
except ValueError as e:
    # Error when initializing the client.
    print(f"ERROR: API Client initialization failed: {e}")
    api_client = None

# Ensure the database is initialized (creates tables if they don't exist).
initialize_db()
    
def main():
    # Start of the WoW Token price tracking task.
    print(f"\n--- WoW Token Tracker: Starting Data Fetch Task ---")

    if api_client is None:
        # Stop the task if the API client failed to initialize earlier.
        print("ERROR: API client is not initialized. Skipping data fetch.")
        return

    try:
        # Fetch the current WoW Token price data from the Blizzard API.
        data = api_client.fetch_wow_token_price()

        # Extract the price value from the response data.
        price = data["price"]

        # Save the fetched price to the database.
        save_price(price)

    except requests.exceptions.RequestException as e:
        # Error during the API request.
        print(f"ERROR: API request failed (Network/HTTP error): {e}")
    except KeyError as e:
        # Error if the expected 'price' key is missing from the API response.
        print(f"ERROR: Failed to parse API response. Missing expected key: {e}")
    except Exception as e:
        # Catch any other unexpected errors during the tracking process.
        print(f"An unexpected error occurred during the tracking process: {e}")


def run_schedule():
    # Schedule the 'main' function to run at a regular interval.
    schedule.every(20).minutes.do(main)

    # Continuous loop to check for and execute pending scheduled jobs.
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Execute 'main' immediately to get the first data point upon startup.
    main()

    # Start the scheduler in a separate thread to run the tracking task in the background.
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()

    # Start the Dash web dashboard, which serves the data visualization.
    app.run(debug=False)