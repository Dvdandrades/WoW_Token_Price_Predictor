import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import json
from pathlib import Path


class BlizzardAPIClient:
    """
    A client for the Blizzard API, handling OAuth2 client credentials flow
    for token generation, token caching (multiple regions), and making API requests.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        region: str,
        locale: str,
        token_cache_file: Path,
    ):
        """
        Initializes the client with credentials and configuration.
        """
        if not client_id or not client_secret:
            raise ValueError(
                "CLIENT_ID and CLIENT_SECRET must be set in environment variables."
            )

        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.region = region
        self.locale: str = locale
        self.token_cache_file: Path = (
            token_cache_file.parent / f"token_cache_{region}.json"
        )

        self.oauth_url = "https://oauth.battle.net/token"
        self.api_base_url = f"https://{region}.api.blizzard.com"
        self.namespace = f"dynamic-{region}"
        self._access_token = None

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
        """
        Attempts to load a valid access token from the local cache file.
        Returns the token string if valid, otherwise returns None.
        """
        if self.token_cache_file.exists():
            try:
                with open(self.token_cache_file, "r") as f:
                    data = json.load(f)
                    if time.time() < data.get("expiry", 0):
                        self._access_token = data.get("access_token")
                        return self._access_token
                    else:
                        try:
                            self.token_cache_file.unlink()
                        except OSError:
                            pass
            except json.JSONDecodeError:
                pass
        self._access_token = None
        return None

    def _save_token_cache(self, token: str, expiry: int):
        """
        Saves the new access token and its calculated expiry time to the cache file.
        """
        self.token_cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "access_token": token,
            "expiry": time.time() + expiry,
        }
        with open(self.token_cache_file, "w") as f:
            json.dump(data, f)
        self._access_token = token

    def get_access_token(self) -> str:
        """
        Retrieves a valid access token, first checking memory, then cache,
        and finally requesting a new one from the Blizzard OAuth server if necessary.
        """

        cached_token = self._load_token_cache()
        if cached_token:
            return cached_token

        data = {"grant_type": "client_credentials"}

        try:
            response = self.session.post(
                self.oauth_url, data=data, auth=(self.client_id, self.client_secret)
            )
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to obtain access token: {e}"
            )

        token_data = response.json()
        token = token_data.get("access_token")
        expiry = token_data.get("expires_in", 3600)

        self._save_token_cache(token, expiry)
        return token

    def fetch_wow_token_price(self) -> int:
        """
        Fetches the current WoW Token price from the Blizzard Game Data API.
        The price is returned in copper (e.g., 25000000 for 250k gold).
        """
        try:
            access_token = self.get_access_token()
        except (ValueError, requests.exceptions.RequestException) as e:
            raise requests.exceptions.RequestException(
                f"Failed to obtain access token: {e}"
            )

        url = f"{self.api_base_url}/data/wow/token/index"
        params = {
            "namespace": self.namespace,
            "locale": self.locale,
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to fetch WoW Token price: {e}"
            )

        token_data = response.json()
        price = token_data.get("price")

        if price is None:
            raise KeyError(
                f"API response missing 'price' key. Response data: {token_data}"
            )

        return price
