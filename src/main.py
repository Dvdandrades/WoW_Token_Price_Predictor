from api_client import get_access_token, fetch_wow_token_price

def main():
    print("=== WoW Token Tracker ===")

    print("[1] Obteniendo token de acceso...")
    token = get_access_token()
    print(token)

    print("[2] Obteniendo precio actual...")
    data = fetch_wow_token_price(token)
    price = data["price"]
    print(price)


main()