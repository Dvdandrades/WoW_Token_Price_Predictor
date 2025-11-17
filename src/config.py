from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

CLIENT_ID: str = os.getenv("CLIENT_ID")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET")
DEFAULT_REGION: str = os.getenv("REGION", "eu")
LOCALE: str = "en_US"

TOKEN_CACHE_FILE: Path = PROJECT_ROOT / "data" / "token_cache.json"
DB_PATH: Path = PROJECT_ROOT / "data" / "wow_token_prices.db"

COOPER_PER_GOLD: int = 10000

CACHE_TIMEOUT_MINUTES: int = 19
EMA_SPAN_DAYS: int = 7

COLOR_INCREASE: str = "#17B897"
COLOR_DECREASE: str = "#FF6347"

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
