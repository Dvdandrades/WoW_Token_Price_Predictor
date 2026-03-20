import time
import schedule
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from api_client import BlizzardAPIClient
from data_manager import save_price, initialize_db
from config import CLIENT_ID, CLIENT_SECRET, REGION_OPTIONS, LOCALE, TOKEN_CACHE_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def run_collection_job(api_client: BlizzardAPIClient) -> None:
    """
    Fetches the WoW token price for a specific region and persists it.
 
    Args:
        api_client: A BlizzardAPIClient configured for the target region.
    """
    region = api_client.region
    logging.info(f"Starting price collection for region: {region}")

    try:
        price = api_client.fetch_wow_token_price()
        save_price(price, region)
        logging.info(f"Price saved for {region}: {price} copper.")
    except requests.exceptions.RequestException as e:
        logging.error(f"API error for {region}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error for {region}: {e}")


def run_all_regions(api_clients: dict[str, BlizzardAPIClient]) -> None:
    """
    Runs the collection job for all regions in parallel using a thread pool.
 
    Args:
        api_clients: A mapping of region identifier to its API client.
    """
    with ThreadPoolExecutor(max_workers=len(api_clients)) as executor:
        futures = {
            executor.submit(run_collection_job, client): region
            for region, client in api_clients.items()
        }
        for future in as_completed(futures):
            region = futures[future]
            exc = future.exception()
            if exc:
                logging.error(f"Unhandled exception in thread for {region}: {exc}")


def _build_api_clients() -> dict[str, BlizzardAPIClient]:
    """
    Initializes a BlizzardAPIClient for each configured region.
 
    Returns:
        A dict mapping region identifiers to their respective API clients.
        Regions that fail to initialize are skipped with an error log.
    """
    clients = {}
    for region_option in REGION_OPTIONS:
        region = region_option["value"]
        try:
            clients[region] = BlizzardAPIClient(
                CLIENT_ID, CLIENT_SECRET, region, LOCALE, TOKEN_CACHE_FILE
            )
            logging.info(f"Client initialized for region: {region}")
        except ValueError as e:
            logging.error(f"Failed to initialize client for {region}: {e}")
    return clients
    

def start_worker():
    """
    Entry point for the worker process.
 
    Initializes the database, builds API clients, runs an immediate collection
    pass for all regions in parallel, then schedules periodic runs.
    """
    initialize_db()
    logging.info("Database initialized.")

    api_clients = _build_api_clients()
    if not api_clients:
        logging.critical("No API clients could be initialized. Exiting.")
        return

    # Immediate collection pass on startup
    run_all_regions(api_clients)

    # Schedule the parallel job every 20 minutes
    schedule.every(20).minutes.do(run_all_regions, api_clients=api_clients)
    logging.info("Scheduler started. Waiting for tasks...")

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logging.critical(f"Scheduler error: {e}")
        time.sleep(1)


if __name__ == "__main__":
    start_worker()
