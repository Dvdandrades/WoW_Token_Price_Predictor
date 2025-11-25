from pathlib import Path
from dotenv import load_dotenv
import os

# Define the root directory of the project
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from the .env file located in the project root
load_dotenv(PROJECT_ROOT / ".env")

# API Credentials and Defaults
CLIENT_ID: str = os.getenv("CLIENT_ID")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET")
DEFAULT_REGION: str = os.getenv("REGION", "eu")
LOCALE: str = "en_US"

# File Paths
# Cache file for Blizzard OAuth tokens
TOKEN_CACHE_FILE: Path = PROJECT_ROOT / "data" / "token_cache.json"
# Path to the SQLite database file
DB_PATH: Path = PROJECT_ROOT / "data" / "wow_token_prices.db"

# Constants
# Conversion factor
COPPER_PER_GOLD: int = 10000

# Data caching duration for the Dash application
CACHE_TIMEOUT_MINUTES: int = 19
# Number of days used for the Exponential Moving Average calculation
EMA_SPAN_DAYS: int = 7

# Visualization Colors
COLOR_INCREASE: str = "#17B897"  # Green for positive change
COLOR_DECREASE: str = "#FF6347"  # Red for negative change

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
