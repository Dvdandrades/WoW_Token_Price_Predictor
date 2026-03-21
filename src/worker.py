import logging
import signal
import sys
import functools
import threading
import requests
import schedule

from concurrent.futures import ThreadPoolExecutor, as_completed
from pythonjsonlogger.json import JsonFormatter

from api_client import BlizzardAPIClient
from config import LOCALE, REGION_OPTIONS, TOKEN_CACHE_FILE, get_settings
from db_writer import initialize_db, save_price

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        rename_fields={"levelname": "level", "asctime": "ts"},
    )
)
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# Shutdown coordination
_shutdown_event = threading.Event()


def _handle_signal(signum: int, _frame) -> None:
    logger.info("Shutdown signal (%s) received - stopping worker.", signum)
    _shutdown_event.set()


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# Collection logic
def run_collection_job(api_client: BlizzardAPIClient) -> None:
    """
    Fetch and persist the WoW Token price for a single region.

    Args:
        api_client: A BlizzardAPIClient configured for the target region.
    """
    region = api_client.region
    logger.info("Starting price collection for region: %s", region)

    try:
        price = api_client.fetch_wow_token_price()
        save_price(price, region)
        logger.info("Price saved for %s: %d copper.", region, price)
    except requests.exceptions.RequestException:
        logger.exception("API error for region '%s'.", region)
    except Exception:
        logger.exception("Unexpected error for region '%s'.", region)


def run_all_regions(
    api_clients: dict[str, BlizzardAPIClient], executor: ThreadPoolExecutor
) -> None:
    """
    Execute the collection job for all regions in parallel.

    Args:
        api_clients: Mapping of region identifier → API client.
    """
    futures = {
        executor.submit(run_collection_job, client): region
        for region, client in api_clients.items()
    }
    for future in as_completed(futures):
        region = futures[future]
        exc = future.exception()
        if exc:
            logger.error("Unhandled exception in thread for '%s': %s", region, exc)


# Initialisation helpers
def _build_api_clients() -> dict[str, BlizzardAPIClient]:
    """
    Instantiate one BlizzardAPIClient per configured region.

    Regions that fail to initialise (e.g. missing credentials) are skipped
    and logged rather than aborting the entire worker.

    Returns:
        Dict mapping region value to its client instance.
    """
    clients: dict[str, BlizzardAPIClient] = {}
    for region_option in REGION_OPTIONS:
        region = region_option["value"]
        try:
            clients[region] = BlizzardAPIClient(
                get_settings().client_id,
                get_settings().client_secret,
                region,
                LOCALE,
                TOKEN_CACHE_FILE,
            )
            logger.info("API client initialised for region: %s", region)
        except ValueError:
            logger.exception("Failed to initialise client for region '%s'.", region)

    return clients


# Entry point
def start_worker() -> None:
    """
    Initialise the database, build clients, run an immediate collection pass,
    schedule periodic runs, then block until a shutdown signal is received.
    """
    initialize_db()

    api_clients = _build_api_clients()
    if not api_clients:
        logger.critical("No API clients could be initialised. Exiting.")
        return

    with ThreadPoolExecutor(max_workers=len(api_clients)) as executor:
        job = functools.partial(run_all_regions, api_clients, executor)

        job()

        interval = get_settings().worker_interval_minutes
        schedule.every(interval).minutes.do(job)
        logger.info(
            "Scheduler started — collecting every %d minutes. "
            "Send SIGTERM or SIGINT to stop.",
            interval,
        )

        while not _shutdown_event.is_set():
            try:
                schedule.run_pending()
            except Exception:
                logger.exception("Scheduler error.")
            _shutdown_event.wait(timeout=1)

    logger.info("Worker stopped cleanly.")


if __name__ == "__main__":
    start_worker()
