from dash import Input, Output
import pandas as pd
from data_handler import get_db_mtime, load_data
from figures import create_token_line_plot


def register_callbacks(app, cache):
    """
    Registers all application callbacks with the Dash app instance.
    The cache object is required for the data loading function.
    """
    @app.callback(
        (
        Output("token-line-plot", "figure"),
        Output("date-range", "min_date_allowed"),
        Output("date-range", "max_date_allowed"),
        Output("date-range", "start_date"),
        Output("date-range", "end_date"),
        Output("last-updated-time", "children"),
        Output("current-price-value", "children"),
        Output("average-price-value", "children"),
        Output("highest-price-value", "children"),
        Output("lowest-price-value", "children"),
        ),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("interval-check", "n_intervals"), # Triggered by the 5-minute interval component
    )
    def update_graph(start_date, end_date, n_intervals):
        # Data Loading & Caching
        # Retrieve the file's modification time for the cache invalidation key.
        mtime = get_db_mtime()
        # Load the cached or fresh data from the database.
        df = load_data(mtime, cache)

        last_updated_text = "Last updated: N/A"
        current_price_display = "N/A"
        average_price_display = "N/A"
        highest_price_display = "N/A"
        lowest_price_display = "N/A"

        # No Data Available Check
        if df.empty:
            default_figure = {"data": [], "layout": {"title": {"text": "No Data Available", "x": 0.5}}}
            return (
                default_figure,
                None, None, None, None,
                last_updated_text,
                current_price_display,
                average_price_display,
                highest_price_display,
                lowest_price_display
            )
        
        # Calculate Metadata for Display
        # Determine the latest update time and price for the stat cards.
        last_updated_time_str = df["datetime"].max().strftime("%Y-%m-%d %H:%M:%S")
        last_updated_text = f"Last updated: {last_updated_time_str}"
        current_price_display = f"{df["price_gold"].iloc[-1]:,}"

        # Date Picker Range Configuration
        # Establish the date range boundaries based on the loaded data.
        min_date = df["datetime"].min().date().isoformat()
        max_date = df["datetime"].max().date().isoformat()

        # Set default/current date range for the plot.
        new_start_date = start_date or min_date
        new_end_date = end_date or max_date

        # Convert selected dates for filtering. Add one day to end_dt for inclusive filtering.
        start_dt = pd.to_datetime(new_start_date)
        end_dt = pd.to_datetime(new_end_date) + pd.Timedelta(days=1)

        # Filter Data
        date_filtered = df[(df["datetime"] >= start_dt) & (df["datetime"] < end_dt)]

        # Calculate Average Price for Display
        if not date_filtered.empty:
            avg_price = date_filtered["price_gold"].mean()
            average_price_display = f"{round(avg_price):,}"

            highest_price = date_filtered["price_gold"].max()
            lowest_price = date_filtered["price_gold"].min()

            highest_price_display = f"{highest_price:,}"
            lowest_price_display = f"{lowest_price:,}"

        # No Data in Range Check
        if date_filtered.empty:
            default_figure = {"data": [], "layout": {"title": {"text": "No Data Available", "x": 0.5}}}
            return (
                default_figure,
                min_date, max_date, new_start_date, new_end_date,
                last_updated_text,
                current_price_display,
                average_price_display,
                highest_price_display,
                lowest_price_display
            )

        # Generate Plot and Return
        line_figure = create_token_line_plot(date_filtered)

        # Return the figure and the updated date picker/stat card properties.
        return (
            line_figure, 
            min_date, max_date, new_start_date, new_end_date, 
            last_updated_text, 
            current_price_display, 
            average_price_display, 
            highest_price_display, 
            lowest_price_display
            )