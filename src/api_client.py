import requests
import os
import time
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from the project’s root .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Retrieve Blizzard API credentials and configuration from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REGION = os.getenv("REGION", "eu")  # Default to EU if unspecified
LOCALE = "en_US"

# Construct Blizzard API endpoints based on the selected region
OAUTH_URL = f"https://{REGION}.battle.net/oauth/token"  # OAuth2 token endpoint
API_BASE_URL = f"https://{REGION}.api.blizzard.com"     # Base API URL
NAMESPACE = f"dynamic-{REGION}"                         # Defines data type/region context

# Define where to cache OAuth tokens for reuse between runs
TOKEN_CACHE_FILE = PROJECT_ROOT / "data" / "token_cache.json"


def load_token_cache():
    """
    Load a cached OAuth2 access token if it exists and is still valid.

    The cache file stores both the token and its expiry timestamp. If the
    cached token is still valid (not expired), it will be returned.

    Returns:
        str | None: The cached access token if valid, otherwise None.
    """
    if TOKEN_CACHE_FILE.exists():
        with open(TOKEN_CACHE_FILE, 'r') as f:
            data = json.load(f)
            # Return cached token only if it's still within its valid timeframe
            if time.time() < data.get('expiry', 0):
                return data.get('access_token')
    return None


def save_token_cache(token, expiry):
    """
    Save an OAuth2 access token and its expiry time to a local cache file.

    Args:
        token (str): The OAuth2 access token string.
        expiry (int): Token lifetime in seconds.
    """
    TOKEN_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "access_token": token,
        # Refresh token slightly before actual expiration
        "expiry": time.time() + expiry - 60
    }

    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump(data, f)


def get_access_token():
    """
    Retrieve a valid OAuth2 access token for Blizzard's API.

    Checks for a cached token first. If none is found or it's expired,
    a new token is requested using the 'client_credentials' grant type.

    Returns:
        str: A valid OAuth2 access token.

    Raises:
        ValueError: If CLIENT_ID or CLIENT_SECRET is missing.
        requests.exceptions.RequestException: If the token request fails.
    """
    # Use cached token if available
    token = load_token_cache()
    if token:
        return token

    # Ensure required credentials are set
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment variables.")

    # Prepare OAuth2 token request payload
    json_data = {'grant_type': 'client_credentials'}

    try:
        response = requests.post(OAUTH_URL, json=json_data, auth=(CLIENT_ID, CLIENT_SECRET))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Failed to obtain access token: {e}")

    token_data = response.json()
    token = token_data.get("access_token")
    expiry = token_data.get("expires_in", 3600)  # Default lifespan: 1 hour

    # Cache token for future reuse
    save_token_cache(token, expiry)
    return token


def fetch_wow_token_price(access_token=None, locale=LOCALE):
    """
    Retrieve the current World of Warcraft Token price via Blizzard's API.

    Args:
        access_token (str, optional): OAuth2 access token. If None, a new one is fetched.
        locale (str, optional): Response locale (default: 'en_US').

    Returns:
        dict: The JSON response containing WoW Token data such as price and last update time.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
        KeyError: If the 'price' field is missing in the response.
    """
    # Automatically obtain a token if not provided
    if access_token is None:
        access_token = get_access_token()

    # WoW Token API endpoint
    url = f"{API_BASE_URL}/data/wow/token/index"

    # Query parameters for data and locale context
    params = {
        'namespace': NAMESPACE,
        'locale': locale,
    }

    # Include bearer token in authorization header
    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Failed to fetch WoW Token price: {e}")

    token_data = response.json()

    if "price" not in token_data:
        raise KeyError(f"API response missing 'price' key. Response data: {token_data}")

    return token_data
