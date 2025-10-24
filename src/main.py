from api_client import get_access_token, fetch_wow_token_price
from data_manager import save_price
from dashboard import app
import time
import schedule
import threading

def main():
    """Fetches, saves, and plots the latest WoW Token price."""
    print(f"\n--- WoW Token Tracker ---")

    try:
        print("Getting access token...")
        token = get_access_token()

        print("Fetching WoW Token price...")
        data = fetch_wow_token_price(token)
        price = data["price"]
        save_price(price)
        
    except Exception as e:
        print(f"An error occurred during tracking: {e}")

def run_schedule():
    schedule.every(20).minutes.do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)

# The `main` function runs every 20 minutes
# The `app.run` command runs the web server indefinitely
if __name__ == "__main__":
    main()
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()
    
    app.run(debug=True)
