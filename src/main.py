from api_client import BlizzardAPIClient
from data_manager import save_price, initialize_db
from app import app
from config import CLIENT_ID, CLIENT_SECRET, REGION_OPTIONS, LOCALE, TOKEN_CACHE_FILE

import time
import schedule
import threading
import requests

initialize_db()

API_CLIENTS = {}
for region_option in REGION_OPTIONS:
    region = region_option["value"]
    try:
        client = BlizzardAPIClient(
            CLIENT_ID, CLIENT_SECRET, region, LOCALE, TOKEN_CACHE_FILE
        )
        API_CLIENTS[region] = client
    except ValueError as e:
        print(f"ERROR: Client initialization failed for region {region}: {e}")


def main(api_client: BlizzardAPIClient):
    region = api_client.region

    # Start of the WoW Token price tracking task.
    try:
        price = api_client.fetch_wow_token_price()
        save_price(price, api_client.region)

    except requests.exceptions.RequestException as e:
        print(f"ERROR: API request failed for {region}: {e}")
    except Exception as e:
        print(
            f"An unexpected error occurred during the tracking process for {region}: {e}"
        )


def run_schedule():
    for region, client in API_CLIENTS.items():
        schedule.every(20).minutes.do(main, api_client=client)

    # Continuous loop to check for and execute pending scheduled jobs.
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"CRITICAL SCHEDULER ERROR: {e}")
        time.sleep(1)


if __name__ == "__main__":    
    # Start the scheduler in a separate thread to run the tracking task in the background.
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()

    for client in API_CLIENTS.values():
        threading.Thread(target=main, args=(client,)).start()

    # Start the Dash web dashboard, which serves the data visualization.
    app.run(debug=False)
