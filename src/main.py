from api_client import get_access_token, fetch_wow_token_price
from data_manager import save_price
from dashboard import app
import time
import schedule
import threading

def main():
    print(f"\n--- WoW Token Tracker ---")

    try:
        # Obtain the OAuth access token required for the Blizzard API
        print("Getting access token...")
        token = get_access_token()

        # Fetch the current WoW Token price using the access token
        print("Fetching WoW Token price...")
        data = fetch_wow_token_price(token)
        price = data["price"]
        
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
