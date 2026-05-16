import logging
import time
import json
import os
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BlizzardAPIClient:
    """
    Client for the Blizzard Game Data API.

    Handles OAuth2 client-credentials token lifecycle (in-memory check →
    file cache → fresh request) and provides a single public method to
    fetch the current WoW Token price.

    Each region gets its own token cache file so concurrent workers do not
    overwrite each other's tokens.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        region: str,
        locale: str,
        token_cache_file: Path,
    ) -> None:
        if not client_id or not client_secret:
            raise ValueError(
                "CLIENT_ID and CLIENT_SECRET must be set in environment variables."
            )

        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.region: str = region
        self.locale: str = locale
        self.token_cache_file: Path = (
            token_cache_file.parent / f"token_cache_{region}.json"
        )

        self.oauth_url: str = "https://oauth.battle.net/token"
        self.api_base_url: str = f"https://{region}.api.blizzard.com"
        self.namespace: str = f"dynamic-{region}"
        self._access_token: str | None = None
        self._token_expiry: float = 0.0

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _load_token_cache(self) -> str | None:
        """Return a cached token if it exists and has not expired."""
        if not self.token_cache_file.exists():
            return None
        try:
            with open(self.token_cache_file) as f:
                data = json.load(f)
                if time.time() < data.get("expiry", 0):
                    self._access_token = data["access_token"]
                    return self._access_token
                # Token expired — remove stale file
                self.token_cache_file.unlink(missing_ok=True)
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            logger.warning("Could not read token cache for %s: %s", self.region, exc)
        self._access_token = None
        return None

    def _save_token_cache(self, token: str, expires_in: int) -> None:
        """Persist the token and its absolute expiry timestamp to disk."""
        self.token_cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "access_token": token,
            "expiry": time.time() + expires_in,
        }
        with open(self.token_cache_file, "w") as f:
            json.dump(data, f)
        os.chmod(self.token_cache_file, 0o600)
        self._token_expiry = time.time() + expires_in
        self._access_token = token

    def get_access_token(self) -> str:
        """
        Return a valid access token, fetching a new one from Blizzard only
        when the cached one is absent or expired.

        Raises:
            requests.exceptions.RequestException: On network or API errors.
        """
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token
        cached = self._load_token_cache()
        if cached:
            return cached

        logger.debug("Requesting new OAuth token for region %s.", self.region)
        try:
            response = self.session.post(
                self.oauth_url,
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise requests.exceptions.RequestException(
                f"Failed to obtain access token for {self.region}: {exc}"
            ) from exc

        token_data = response.json()
        token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._save_token_cache(token, expires_in)
        return token

    def fetch_wow_token_price(self) -> int:
        """
        Return the current WoW Token price in copper.

        Raises:
            requests.exceptions.RequestException: On token or HTTP errors.
            KeyError: If the API response does not contain the 'price' key.
        """
        access_token = self.get_access_token()

        url = f"{self.api_base_url}/data/wow/token/index"
        params = {
            "namespace": self.namespace,
            "locale": self.locale,
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise requests.exceptions.RequestException(
                f"Failed to fetch WoW Token price for {self.region}: {exc}"
            ) from exc

        token_data = response.json()
        price = token_data.get("price")
        if price is None:
            raise KeyError(f"API response missing 'price' key. Response: {token_data}")
        return price
