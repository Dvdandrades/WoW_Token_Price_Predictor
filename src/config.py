from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DEFAULT_REGION = os.getenv("REGION", "eu")
LOCALE = "en_US"

TOKEN_CACHE_FILE = PROJECT_ROOT / "data" / "token_cache.json"
DB_PATH = PROJECT_ROOT / "data" / "wow_token_prices.db"

COOPER_PER_GOLD = 10000

CACHE_TIMEOUT_MINUTES = 19
EMA_SPAN_DAYS = 7

COLOR_INCREASE = "#17B897"
COLOR_DECREASE = "#FF6347"

DAYS_OPTIONS = [
    {"label": "3 Days", "value": 3},
    {"label": "7 Days", "value": 7},
    {"label": "14 Days", "value": 14},
]
DEFAULT_DAYS_FILTER = 3

REGION_OPTIONS = [
    {"label": "Europe (EU)", "value": "eu"},
    {"label": "United States (US)", "value": "us"},
    {"label": "Korea (KR)", "value": "kr"},
    {"label": "Taiwan (TW)", "value": "tw"},
]