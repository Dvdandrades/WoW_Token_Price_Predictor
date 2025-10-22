import requests
import os
import time
import json
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Retrieve Blizzard API credentials and configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REGION = os.getenv("REGION", "eu")  # Defaults to EU region if not specified

# Construct API endpoint URLs and namespace for the selected region
OAUTH_URL = f"https://{REGION}.battle.net/oauth/token"
API_BASE_URL = f"https://{REGION}.api.blizzard.com"
NAMESPACE = f"dynamic-{REGION}"

# Token cache file
TOKEN_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "token_cache.json"

def load_token_cache():
    if TOKEN_CACHE_FILE.exists():
        with open(TOKEN_CACHE_FILE, 'r') as f:
            data = json.load(f)
            if time.time() < data.get('expiry', 0):
                return data.get('access_token')  
    return None

def save_token_cache(token, expiry):
    data = {
        "access_token": token,
        "expiry": time.time() + expiry - 60  # Refresh 1 minute before expiry
    }
    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump(data, f)

def get_access_token():
    """
    Obtain a cached OAuth2 access token or request a new one if expired.

    The function uses the 'client_credentials' grant type, which is suitable
    for server-to-server authentication.

    Returns:
        str: A valid access token to authenticate subsequent API requests.

    Raises:
        requests.exceptions.HTTPError: If the API call fails (e.g., invalid credentials).
    """

    token = load_token_cache()
    if token:
        return token
    
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment variables.")

    # Request body for OAuth2 client credentials flow
    data = {
        'grant_type': 'client_credentials'
    }

    # Make a POST request to the Battle.net OAuth token endpoint
    response = requests.post(OAUTH_URL, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    response.raise_for_status()  # Raise an exception if the request failed
    token_data = response.json()

    token = token_data['access_token']
    expiry = token_data.get('expires_in', 3600)  # Default to 1 hour if not provided

    save_token_cache(token, expiry)

    return token

def fetch_wow_token_price(access_token=None, locale='en_US'):
    """
    Fetch the current World of Warcraft Token price from Blizzard's Game Data API.

    Args:
        access_token (str): The OAuth2 access token obtained from get_access_token().
        locale (str, optional): The desired language/region code (default: 'en_US').

    Returns:
        dict: A JSON response containing WoW Token data, including price and last update time.

    Raises:
        requests.exceptions.HTTPError: If the API call fails (e.g., invalid token or bad parameters).
    """

    if access_token is None:
        access_token = get_access_token()

    # Endpoint for WoW Token market data
    url = f"{API_BASE_URL}/data/wow/token/index"

    # Query parameters for the API call
    params = {
        'namespace': NAMESPACE,
        'locale': locale,
    }

    # HTTP headers, including the bearer token for authentication
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Make the GET request to the Blizzard API
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # Raise exception on HTTP error

    # Return the full JSON response (includes price, last_updated_timestamp, etc.)
    return response.json()