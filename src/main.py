from api_client import BlizzardAPIClient, CLIENT_ID, CLIENT_SECRET, REGION, LOCALE, TOKEN_CACHE_FILE
from data_manager import save_price
from dashboard import app
import time
import schedule
import threading

def main():
    """
    The main data collection function. 
    It fetches the current WoW Token price and saves it to the database.
    """
    print(f"\n--- WoW Token Tracker ---")

    try:

        # Initialize the Blizzard API client with necessary credentials and settings.
        client = BlizzardAPIClient(CLIENT_ID, CLIENT_SECRET, REGION, LOCALE, TOKEN_CACHE_FILE)

        # Fetch the current WoW Token price using the access token
        print("Fetching WoW Token price...")
        data = client.fetch_wow_token_price()
        price = data["price"] # Extract the price value from the returned data
        
        # Save the fetched price data to the database
        save_price(price)
        
    except Exception as e:
        # Log any errors that occur during the fetch/save process
        print(f"An error occurred during tracking: {e}")

def run_schedule():
    """
    Sets up the recurring task for data collection and keeps the scheduler running.
    This function is executed in a separate thread to prevent blocking the web server.
    """
    # Schedule the 'main' function to run every 20 minutes
    schedule.every(20).minutes.do(main)
    
    # Loop continuously to check for and execute pending scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Run 'main' immediately to fetch the first data point upon startup
    main()
    
    # Start the scheduler in a separate, non-blocking thread. 
    # daemon=True ensures the thread exits when the main process exits.
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()
    
    # Start the Flask web dashboard, which runs indefinitely on the main thread.
    app.run(debug=False)
