import matplotlib.pyplot as plt
import os

def plot_history(df):
    """
    Plot the historical World of Warcraft token prices over time.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing at least two columns:
        - 'datetime': timestamps of the recorded prices
        - 'price_gold': corresponding token prices in gold

    The function generates a line plot showing how the token price changes
    over time and saves it as 'plot.png' in the current working directory.
    """
    
    # Determine the directory where this script (plotter.py) is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build a path to the 'data' folder one level up
    data_dir = os.path.join(script_dir, "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    # Save plot in that directory
    save_path = os.path.join(data_dir, "plot.png")

    # Create a new figure with a defined size
    plt.figure(figsize=(10, 5))
    
    # Plot price data against datetime, with circular markers and a thin line
    plt.plot(df['datetime'], df['price_gold'], marker='o', linewidth=1)
    
    # Add a descriptive title and axis labels
    plt.title('WoW Token Price History')
    plt.xlabel('Date')
    plt.ylabel('Price (Gold)')
    
    # Enable grid lines to improve readability
    plt.grid(True)
    
    # Automatically adjust layout to prevent label overlap
    plt.tight_layout()
    
    # Save the resulting plot as an image file
    plt.savefig(save_path)