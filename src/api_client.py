import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import json
from pathlib import Path


class BlizzardAPIClient:
    """
    A client for the Blizzard API, handling OAuth2 client credentials flow
    for token generation, token caching, and making API requests
    with built-in retry logic.
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

        Args:
            client_id: The client ID for the Blizzard API.
            client_secret: The client secret for the Blizzard API.
            region: The region identifier.
            locale: The locale for API requests.
            token_cache_file: Base path for the token cache file.

        Raises:
            ValueError: If client_id or client_secret are not provided.
        """
        if not client_id or not client_secret:
            raise ValueError(
                "CLIENT_ID and CLIENT_SECRET must be set in environment variables."
            )

        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.region = region
        self.locale: str = locale
        # Create a region-specific cache file path
        self.token_cache_file: Path = (
            token_cache_file.parent / f"token_cache_{region}.json"
        )

        self.oauth_url = "https://oauth.battle.net/token"
        self.api_base_url = f"https://{region}.api.blizzard.com"
        # Dynamic namespace is required for WoW Game Data APIs
        self.namespace = f"dynamic-{region}"
        self._access_token = None

        # Configure retry strategy for transient server errors
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
        Attempts to load a valid access token from the local, region-specific cache file.

        Returns:
            The token string if valid and loaded, otherwise None.
        """
        if self.token_cache_file.exists():
            try:
                with open(self.token_cache_file, "r") as f:
                    data = json.load(f)
                    # Check if the token's expiry time is in the future
                    if time.time() < data.get("expiry", 0):
                        self._access_token = data.get("access_token")
                        return self._access_token
                    else:
                        # Token expired, attempt to delete the stale cache file
                        try:
                            self.token_cache_file.unlink()
                        except OSError:
                            pass  # Ignore if deletion fails
            except json.JSONDecodeError:
                pass  # Ignore if file is corrupted
        self._access_token = None
        return None

    def _save_token_cache(self, token: str, expiry: int):
        """
        Saves the new access token and its calculated absolute expiry timestamp
        to the cache file.

        Args:
            token: The new access token string.
            expiry: The token's time-to-live in seconds.
        """
        # Ensure the directory for the cache file exists
        self.token_cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "access_token": token,
            # Calculate absolute expiry time
            "expiry": time.time() + expiry,
        }
        with open(self.token_cache_file, "w") as f:
            json.dump(data, f)
        self._access_token = token

    def get_access_token(self) -> str:
        """
        Retrieves a valid access token, checking memory, then cache, and finally
        requesting a new one from the Blizzard OAuth server if necessary.

        The method implements the OAuth 2.0 Client Credentials flow.

        Returns:
            The valid access token string.

        Raises:
            requests.exceptions.RequestException: If the token request fails due to
                network issues or an API error.
        """

        # Check if token is already loaded
        cached_token = self._load_token_cache()
        if cached_token:
            return cached_token

        # Request a new token
        data = {"grant_type": "client_credentials"}

        try:
            response = self.session.post(
                self.oauth_url, data=data, auth=(self.client_id, self.client_secret)
            )
            response.raise_for_status()  # Raise HTTPError for bad responses
        except requests.exceptions.RequestException as e:
            # Re-raise with a more informative message
            raise requests.exceptions.RequestException(
                f"Failed to obtain access token: {e}"
            )

        token_data = response.json()
        token = token_data.get("access_token")
        # Default to 1 hour if 'expires_in' is missing
        expiry = token_data.get("expires_in", 3600)

        self._save_token_cache(token, expiry)
        return token

    def fetch_wow_token_price(self) -> int:
        """
        Fetches the current WoW Token price from the Blizzard Game Data API.

        The API returns the price in copper.

        Returns:
            The WoW Token price in copper.

        Raises:
            requests.exceptions.RequestException: If token retrieval or price
                fetching fails.
            KeyError: If the API response is missing the 'price' key.
        """
        try:
            access_token = self.get_access_token()
        except (ValueError, requests.exceptions.RequestException) as e:
            # Re-raise with a specific context for token failure
            raise requests.exceptions.RequestException(
                f"Failed to obtain access token: {e}"
            )

        url = f"{self.api_base_url}/data/wow/token/index"
        params = {
            "namespace": self.namespace,
            "locale": self.locale,
        }
        # Set Authorization header with the Bearer token
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = self.session.get(url, params=params, headers=headers)
            # Check for HTTP errors
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to fetch WoW Token price: {e}"
            )

        token_data = response.json()
        price = token_data.get("price")

        if price is None:
            # Guard against unexpected API response structure
            raise KeyError(
                f"API response missing 'price' key. Response data: {token_data}"
            )

        return price
