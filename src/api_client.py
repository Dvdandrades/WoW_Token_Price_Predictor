import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REGION = os.getenv("REGION", "eu")

OAUTH_URL = f"https://{REGION}.battle.net/oauth/token"
API_BASE_URL = f"https://{REGION}.api.blizzard.com"
NAMESPACE = f"dynamic-{REGION}"

def get_access_token():
    data = {
        'grant_type': 'client_credentials'
    }

    response = requests.post(OAUTH_URL, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    response.raise_for_status()
    return response.json()['access_token']

def fetch_wow_token_price(access_token, locale='en_US'):
    url = f"{API_BASE_URL}/data/wow/token/index"
    params = {
        'namespace': NAMESPACE,
        'locale': locale,
    }
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()