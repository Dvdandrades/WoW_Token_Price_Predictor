from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REGION = os.getenv("REGION", "eu")
LOCALE = "en_US"

TOKEN_CACHE_FILE = PROJECT_ROOT / "data" / "token_cache.json"
DB_PATH = PROJECT_ROOT / "data" / "wow_token_prices.db" # Importar esto en data_manager