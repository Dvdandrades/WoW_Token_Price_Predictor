from api_client import get_access_token, fetch_wow_token_price
from data_manager import save_price, load_data
from plotter import plot_history
from dashboard import app
import schedule

def main():
    """Fetches, saves, and plots the latest WoW Token price."""
    print(f"\n--- WoW Token Tracker ---")

    try:
        print("Getting access token...")
        token = get_access_token()

        print("Fetching WoW Token price...")
        data = fetch_wow_token_price(token)
        price = data["price"]
        save_price(price)
        
        print("Loading historical data...")
        # Load data is here primarily to ensure the plotting function works
        df = load_data()

        print("Plotting price history...")
        plot_history(df) # This creates the static plot.png
        
    except Exception as e:
        print(f"An error occurred during tracking: {e}")

# Call once immediately to start
main()

# Schedule the tracking function to run every 20 minutes
schedule.every(20).minutes.do(main)

print("\nScheduler started. Tracking every 20 minutes.")
print("Starting Dash web server in debug mode...")

# The `main` function runs every 20 minutes
# The `app.run` command runs the web server indefinitely
if __name__ == "__main__":
    app.run(debug=True)
