from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.
    All values that may differ between environments live here.
    Structural constants (colours, column lists, UI options) remain as module-level
    literals below — they are not environment-dependent.
    """

    client_id: str = Field(..., validation_alias="CLIENT_ID")
    client_secret: str = Field(..., validation_alias="CLIENT_SECRET")
    region: str = Field("eu", validation_alias="REGION")
    ema_span_days: int = Field(7, validation_alias="EMA_SPAN_DAYS")
    cache_timeout_minutes: int = Field(19, validation_alias="CACHE_TIMEOUT_MINUTES")
    worker_interval_minutes: int = Field(20, validation_alias="WORKER_INTERVAL_MINUTES")

    model_config = {"env_file": PROJECT_ROOT / ".env"}


settings = Settings()


# File Paths
TOKEN_CACHE_FILE: Path = PROJECT_ROOT / "data" / "token_cache.json"
DB_PATH: Path = PROJECT_ROOT / "data" / "wow_token_prices.db"

# Constants
COPPER_PER_GOLD: int = 10_000
LOCALE: str = "en_US"
EMPTY_DF_COLUMNS: list[str] = [
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

DEFAULT_REGION: str = settings.region
