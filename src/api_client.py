import requests
import os
import time
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from the project's root .env file
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Retrieve Blizzard API credentials and configuration from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REGION = os.getenv("REGION", "eu")  # Defaults to EU region if unspecified

# Construct key Blizzard API URLs based on the selected region
OAUTH_URL = f"https://{REGION}.battle.net/oauth/token"        # OAuth2 token endpoint
API_BASE_URL = f"https://{REGION}.api.blizzard.com"            # Base API URL for data requests
NAMESPACE = f"dynamic-{REGION}"                                # Namespace defines data type/region context

# Define token cache file location for reusing access tokens between runs
TOKEN_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "token_cache.json"

def load_token_cache():
    """
    Load a previously saved OAuth access token from the cache file if valid.

    The cache includes both the token and its expiry timestamp. If the token
    is still valid (i.e., not expired), it is returned; otherwise, None is returned.

    Returns:
        str or None: Cached access token if valid, otherwise None.
    """
    if TOKEN_CACHE_FILE.exists():
        with open(TOKEN_CACHE_FILE, 'r') as f:
            data = json.load(f)
            # Check token validity against current time
            if time.time() < data.get('expiry', 0):
                return data.get('access_token')  
    return None


def save_token_cache(token, expiry):
    """
    Save the newly obtained OAuth access token to a local cache file.

    Args:
        token (str): The OAuth2 access token string.
        expiry (int): Token lifespan in seconds.
    """
    # Ensure the cache directory exists before writing
    TOKEN_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "access_token": token,
        # Subtract 60 seconds to refresh the token slightly before expiration
        "expiry": time.time() + expiry - 60
    }

    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump(data, f)


def get_access_token():
    """
    Obtain a cached OAuth2 access token or request a new one if expired or missing.

    Uses the 'client_credentials' grant type suitable for backend or server-to-server
    communication with Blizzard APIs (no user authentication required).

    Returns:
        str: A valid OAuth2 access token for authenticating Blizzard API requests.

    Raises:
        ValueError: If CLIENT_ID or CLIENT_SECRET is not set.
        requests.exceptions.HTTPError: If the API call fails.
    """
    # Try using a cached token first
    token = load_token_cache()
    if token:
        return token

    # Validate that credentials exist before making a network call
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment variables.")

    # Prepare request payload for OAuth2 'client_credentials' grant
    data = {'grant_type': 'client_credentials'}

    # Request a new token from Blizzard's OAuth2 endpoint
    response = requests.post(OAUTH_URL, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    response.raise_for_status()  # Raise error if authentication fails

    token_data = response.json()
    token = token_data['access_token']
    expiry = token_data.get('expires_in', 3600)  # Fallback to 1 hour if missing

    # Save token locally for reuse
    save_token_cache(token, expiry)

    return token

def fetch_wow_token_price(access_token=None, locale='en_US'):
    """
    Retrieve the current World of Warcraft Token price from Blizzard's Game Data API.

    Args:
        access_token (str, optional): OAuth2 access token. If None, a new one is fetched.
        locale (str, optional): Desired response locale.

    Returns:
        dict: JSON response containing WoW Token data (price, last_updated_timestamp, etc.).

    Raises:
        requests.exceptions.HTTPError: If the API call fails (e.g., invalid token, bad parameters).
    """
    # Automatically fetch a token if one wasn't provided
    if access_token is None:
        access_token = get_access_token()

    # Construct endpoint for WoW Token data
    url = f"{API_BASE_URL}/data/wow/token/index"

    # Attach required query parameters
    params = {
        'namespace': NAMESPACE,  # Selects the correct data region/type
        'locale': locale,        # Defines response language
    }

    # Include the bearer token in request headers for authentication
    headers = {'Authorization': f'Bearer {access_token}'}

    # Perform the API call
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # Raise exception if API returns an error

    # Return parsed JSON response with WoW token data
    return response.json()
