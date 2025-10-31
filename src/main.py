from api_client import BlizzardAPIClient, CLIENT_ID, CLIENT_SECRET, REGION, LOCALE, TOKEN_CACHE_FILE
from data_manager import save_price, initialize_db
from dashboard import app
import time
import schedule
import threading
import requests

try:
    # Initialize the Blizzard API Client with credentials and regional settings.
    api_client = BlizzardAPIClient(CLIENT_ID, CLIENT_SECRET, REGION, LOCALE, TOKEN_CACHE_FILE)
except ValueError as e:
    # Error when initializing the client.
    print(f"ERROR: API Client initialization failed: {e}")
    api_client = None

def main():
    # Start of the WoW Token price tracking task.
    print(f"\n--- WoW Token Tracker: Starting Data Fetch Task ---")

    if api_client is None:
        # Stop the task if the API client failed to initialize earlier.
        print("ERROR: API client is not initialized. Skipping data fetch.")
        return

    try:
        # Ensure the database is initialized (creates tables if they don't exist).
        initialize_db()

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