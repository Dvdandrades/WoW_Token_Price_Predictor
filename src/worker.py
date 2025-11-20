import time
import schedule
import requests
import logging

from api_client import BlizzardAPIClient
from data_manager import save_price, initialize_db
from config import CLIENT_ID, CLIENT_SECRET, REGION_OPTIONS, LOCALE, TOKEN_CACHE_FILE

# Configure logging to display timestamp, level, and message
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def run_collection_job(api_client: BlizzardAPIClient):
    """
    Fetches the WoW token price for a specific region and saves it to the database.

    Args:
        api_client (BlizzardAPIClient): The client instance configured for a specific region.
    """
    region = api_client.region
    logging.info(f"Starting price collection for region: {region}")

    try:
        # Attempt to fetch the current price from the API
        price = api_client.fetch_wow_token_price()

        # Save the price data using the data manager
        save_price(price, region)
        logging.info(f"Price saved for {region}: {price}")

    except requests.exceptions.RequestException as e:
        # Handle network or API-specific errors
        logging.error(f"API error for {region}: {e}")
    except Exception as e:
        # Handle any other unexpected errors during the process
        logging.error(f"Unexpected error for {region}: {e}")


def start_worker():
    """
    Main entry point for the worker. Initializes the database, creates API clients,
    schedules jobs, and runs the main execution loop.
    """
    # Initialize the database connection
    initialize_db()
    logging.info("Database initialized.")

    api_clients = {}

    # Iterate through all configured regions to set up API clients
    for region_option in REGION_OPTIONS:
        region = region_option["value"]
        try:
            # Initialize the Blizzard API client with credentials and config
            client = BlizzardAPIClient(
                CLIENT_ID, CLIENT_SECRET, region, LOCALE, TOKEN_CACHE_FILE
            )
            api_clients[region] = client
            logging.info(f"Client initialized for region: {region}")
        except ValueError as e:
            logging.error(f"Failed to initialize client for {region}: {e}")

    # Schedule jobs for all successfully initialized clients
    for client in api_clients.values():
        # Run the job immediately so we don't have to wait for the first interval
        run_collection_job(client)

        # Schedule the job to run every 20 minutes
        schedule.every(20).minutes.do(run_collection_job, api_client=client)

    logging.info("Scheduler started. Waiting for tasks...")

    # Main application loop
    while True:
        try:
            # Check and run any pending scheduled tasks
            schedule.run_pending()
        except Exception as e:
            # Catch critical errors to prevent the worker from crashing completely
            logging.critical(f"CRITICAL SCHEDULER ERROR: {e}")

        # Sleep briefly to prevent high CPU usage
        time.sleep(1)


if __name__ == "__main__":
    start_worker()
