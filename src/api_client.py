import requests
import os
from dotenv import load_dotenv

# Load environment variables from a .env file in the project root
load_dotenv()

# Retrieve Blizzard API credentials and configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REGION = os.getenv("REGION", "eu")  # Defaults to EU region if not specified

# Construct API endpoint URLs and namespace for the selected region
OAUTH_URL = f"https://{REGION}.battle.net/oauth/token"
API_BASE_URL = f"https://{REGION}.api.blizzard.com"
NAMESPACE = f"dynamic-{REGION}"


def get_access_token():
    """
    Obtain an OAuth2 access token from Blizzard's Battle.net API.

    The function uses the 'client_credentials' grant type, which is suitable
    for server-to-server authentication.

    Returns:
        str: A valid access token to authenticate subsequent API requests.

    Raises:
        requests.exceptions.HTTPError: If the API call fails (e.g., invalid credentials).
    """
    # Request body for OAuth2 client credentials flow
    data = {
        'grant_type': 'client_credentials'
    }

    # Make a POST request to the Battle.net OAuth token endpoint
    response = requests.post(OAUTH_URL, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    response.raise_for_status()  # Raise an exception if the request failed

    # Parse and return the access token from the JSON response
    return response.json()['access_token']


def fetch_wow_token_price(access_token, locale='en_US'):
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