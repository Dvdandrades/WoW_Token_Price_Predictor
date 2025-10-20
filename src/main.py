from api_client import get_access_token, fetch_wow_token_price
from data_manager import save_price, load_data

def main():
    print("=== WoW Token Tracker ===")

    print("Getting access token...")
    token = get_access_token()
    print(token)

    print("Fetching WoW Token price...")
    data = fetch_wow_token_price(token)
    price = data["price"]
    save_price(price)
    
    print("Loading historical data...")
    df = load_data()


main()