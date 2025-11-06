import requests
import time
import json

# Blizzard API Client Class
class BlizzardAPIClient:
    """
    A client for the Blizzard API, handling OAuth2 client credentials flow
    for token generation, token caching, and making API requests.
    """
    def __init__(self, client_id, client_secret, region, locale, token_cache_file):
        """
        Initializes the client with credentials and configuration.
        """
        if not client_id or not client_secret:
            raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment variables.")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.locale = locale
        self.token_cache_file = token_cache_file

        # Define the static OAuth token endpoint URL.
        self.oauth_url = "https://oauth.battle.net/token"
        # Define the API base URL based on the specified region.
        self.api_base_url = f"https://{region}.api.blizzard.com"
        # Set the dynamic namespace required for many WoW Game Data API endpoints.
        self.namespace = f"dynamic-{region}"
        # Private attribute to store the access token in memory.
        self._access_token = None


    def _load_token_cache(self):
        """
        Attempts to load a valid access token from the local cache file.
        Returns the token string if valid, otherwise returns None.
        """
        if self.token_cache_file.exists():
            try:
                with open(self.token_cache_file, "r") as f:
                    data = json.load(f)
                    # Check if the current time is before the cached expiry time.
                    if time.time() < data.get("expiry", 0):
                        self._access_token = data.get("access_token")
                        return self._access_token
                    else:
                        self.token_cache_file.unlink() # Remove expired cache file.
            # Handle case where the cache file exists but is corrupted/empty.
            except json.JSONDecodeError:
                pass
        self._access_token = None
        return None


    def _save_token_cache(self, token, expiry):
        """
        Saves the new access token and its calculated expiry time to the cache file.
        """
        # Ensure the directory for the cache file exists.
        self.token_cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
           "access_token": token,
           # Calculate absolute expiry time: current time + token lifetime
           "expiry": time.time() + expiry
        }
        with open(self.token_cache_file, 'w') as f:
            json.dump(data, f)
        # Also update the in-memory token.
        self._access_token = token


    def get_access_token(self):
        """
        Retrieves a valid access token, first checking memory, then cache,
        and finally requesting a new one from the Blizzard OAuth server if necessary.
        """
        
        # Check cached token.
        cached_token = self._load_token_cache()
        if cached_token:
            return cached_token
        
        # Request a new token if memory and cache miss.
        data = {"grant_type": "client_credentials"}

        try:
            # Send POST request for token, using HTTP Basic Auth with client_id and client_secret.
            response = requests.post(
                self.oauth_url,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            # Raise an exception for bad status codes (4xx or 5xx).
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Re-raise with a specific message if the request fails.
            raise requests.exceptions.RequestException(f"Failed to obtain access token: {e}")
        
        token_data = response.json()
        token = token_data.get("access_token")
        # Get the token lifetime in seconds, defaulting to 1 hour (3600s).
        expiry = token_data.get("expires_in", 3600)

        # Cache the newly acquired token for future use.
        self._save_token_cache(token, expiry)
        return token

    def fetch_wow_token_price(self):
        """
        Fetches the current WoW Token price from the Blizzard Game Data API.
        The price is returned in copper (e.g., 25000000 for 250k gold).
        """
        try:
            # Ensure we have a valid access token before making the API call.
            access_token = self.get_access_token()
        except (ValueError, requests.exceptions.RequestException) as e:
            # Reraise token acquisition errors to the caller.
            raise requests.exceptions.RequestException(f"Failed to obtain access token: {e}")
        
        # Construct the specific API endpoint URL for the WoW Token index.
        url = f"{self.api_base_url}/data/wow/token/index"

        # Parameters for the API request, including required namespace and locale.
        params = {
            "namespace": self.namespace,
            "locale": self.locale,
        }

        # Authorization header using the Bearer token scheme.
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            # Make the GET request to the WoW API.
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Failed to fetch WoW Token price: {e}")
        
        token_data = response.json()

        price = token_data.get("price")

        # Simple validation to ensure the expected data is present.
        if price is None:
            raise KeyError(f"API response missing 'price' key. Response data: {token_data}")
        
        # Returns the full JSON response containing the 'price' (in copper).
        return price