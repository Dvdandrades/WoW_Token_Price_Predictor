from api_client import get_access_token, fetch_wow_token_price
from data_manager import save_price, load_data
from plotter import plot_history
from dashboard import app
import schedule
import time

def main():
    print("=== WoW Token Tracker ===")

    print("Getting access token...")
    token = get_access_token()

    print("Fetching WoW Token price...")
    data = fetch_wow_token_price(token)
    price = data["price"]
    save_price(price)
    
    print("Loading historical data...")
    df = load_data()

    print("Plotting price history...")
    plot_history(df)

    app.run(debug=True)

"""schedule.every(20).minutes.do(main)

while True:
    schedule.run_pending()
    time.sleep(1)"""

main()