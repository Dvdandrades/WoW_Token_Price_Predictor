from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# API Credentials
CLIENT_ID: str = os.getenv("CLIENT_ID", "")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")

# Fail fast: raise at import time so misconfiguration is obvious immediately, rather than surfacing as a cryptic error during the first API call.
if not CLIENT_ID or not CLIENT_SECRET:
    raise EnvironmentError(
        "Missing required environment variables: CLIENT_ID and CLIENT_SECRET. Must be set in your .env file."
    )

DEFAULT_REGION: str = os.getenv("REGION", "eu")
LOCALE: str = "en_US"

# File Paths
TOKEN_CACHE_FILE: Path = PROJECT_ROOT / "data" / "token_cache.json"
DB_PATH: Path = PROJECT_ROOT / "data" / "wow_token_prices.db"

# Constants
COPPER_PER_GOLD: int = 10000
CACHE_TIMEOUT_MINUTES: int = 19
EMA_SPAN_DAYS: int = 7
EMPTY_DF_COLUMNS = [
    "datetime",
    "price_gold",
    "ema",
    "price_change_abs",
    "price_change_pct",
]

# Visualization Colors
COLOR_INCREASE: str = "#17B897"
COLOR_DECREASE: str = "#FF6347"

# Dropdown Options
DAYS_OPTIONS: list[dict] = [
    {"label": "3 Days", "value": 3},
    {"label": "7 Days", "value": 7},
    {"label": "14 Days", "value": 14},
]
DEFAULT_DAYS_FILTER: int = 3

REGION_OPTIONS: list[dict] = [
    {"label": "Europe (EU)", "value": "eu"},
    {"label": "United States (US)", "value": "us"},
    {"label": "Korea (KR)", "value": "kr"},
    {"label": "Taiwan (TW)", "value": "tw"},
]
