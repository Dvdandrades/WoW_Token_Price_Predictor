from dash import Input, Output, html
import pandas as pd
from data_handler import get_db_mtime, load_data
from figures import create_token_line_plot
from config import COLOR_INCREASE, COLOR_DECREASE

def _determine_date_range(df, start_date_input, end_date_input):
    """
    Determines the available and selected date ranges for the date picker.
    It defaults the start date to 2 days prior to the max available date if no input is provided.
    """
    # Get the earliest and latest available dates in the dataset
    min_date_available = df["datetime"].min().date().isoformat()
    max_date_available = df["datetime"].max().date().isoformat()

    max_date = df["datetime"].max()

    # Calculate a default start date: 2 days before the latest data point
    default_start_date = max_date - pd.Timedelta(days=2)

    min_date = df["datetime"].min()
    # Ensure the default start date is not earlier than the absolute minimum date
    default_start_date = max(default_start_date, min_date)

    default_start_date_str = default_start_date.date().isoformat()

    # Use input dates if they exist, otherwise use the calculated defaults
    new_start_date = start_date_input if start_date_input is not None else default_start_date_str
    new_end_date = end_date_input if end_date_input is not None else max_date_available

    return min_date_available, max_date_available, new_start_date, new_end_date

def _filter_dataframe_by_dates(df, start_date_str, end_date_str):
    """
    Filters the DataFrame to include only rows within the selected date range.
    Adds one day to the end date to ensure the entire day is included (as the input is just the date part).
    """
    # Convert string dates to pandas datetime objects
    start_date = pd.to_datetime(start_date_str)
    # Add one day to the end date to make the range inclusive up to the end of that day
    end_date = pd.to_datetime(end_date_str) + pd.Timedelta(days=1)

    # Filter the DataFrame
    date_filtered = df[(df["datetime"] >= start_date) & (df["datetime"] < end_date)]
    return date_filtered

def _calculate_range_stats(df_filtered):
    """
    Calculates and formats the average, highest, and lowest price within the filtered date range.
    """
    if df_filtered.empty:
        return "N/A", "N/A", "N/A"
    
    # Calculate statistics
    avg_price = df_filtered["price_gold"].mean()
    highest_price = df_filtered["price_gold"].max()
    lowest_price = df_filtered["price_gold"].min()

    # Format numbers with commas for display
    average_price_display = f"{round(avg_price):,}"
    highest_price_display = f"{highest_price:,}"
    lowest_price_display = f"{lowest_price:,}"

    return average_price_display, highest_price_display, lowest_price_display

def _get_empty_state_outputs(df, start_date, end_date):
    """
    Returns default 'N/A' values and an 'No Data' figure when the data frame is empty.
    Used for initial load or if the database file is empty.
    """

    last_updated_text = "Last updated: N/A"
    current_price_display = "N/A"
    average_price_display = "N/A"
    highest_price_display = "N/A"
    lowest_price_display = "N/A"
    price_change_indicators_display = html.Span("N/A", style={"color": "gray"})
    
    # Default figure for when no data is available
    default_figure = {"data": [], "layout": {"title": {"text": "No Data Available", "x": 0.5}}}

    # Returns all required output elements in the correct order for the main callback
    return (
        default_figure,
        None, None, None, None, # No date range updates on empty state
        last_updated_text,
        current_price_display,
        average_price_display,
        highest_price_display,
        lowest_price_display,
        price_change_indicators_display
    )

def _format_price_change_indicators(latest_abs_change, latest_pct_change):
    """
    Formats the absolute and percentage price change indicators as styled Dash HTML components.
    Uses defined colors (COLOR_INCREASE/DECREASE) for styling.
    """
    
    if not pd.isna(latest_abs_change):
        # Determine color and sign based on the absolute change
        is_positive = latest_abs_change >= 0
        color = COLOR_INCREASE if is_positive else COLOR_DECREASE 
        sign = "+" if is_positive else ""

        # Format Absolute Change Span
        abs_change_span = html.Span(
            f"{sign}{round(latest_abs_change):,} Gold",
            style={"color": color, "fontWeight": "bold", "marginRight": "10px"}
        )

        # Format Percentage Change Span
        pct_change_span = html.Span(
            f"({sign}{latest_pct_change:.2f}%)",
            style={"color": color, "fontStyle": "italic"}
        )

        return [abs_change_span, pct_change_span]
    
    else:
        # Handle case where change cannot be calculated
        return html.Span("Change: N/A (Requires two data points)", style={"color": "gray"})


def register_callbacks(app, cache):
    """
    Registers all application callbacks with the Dash app instance.
    The cache object is required for the data loading function.
    """
    @app.callback(
        # Define the 11 outputs for the main graph and stat cards
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
        Output("price_change_indicators", "children"),
        
        # Define the 3 inputs that trigger the callback
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("interval-check", "n_intervals"), # Triggered by the 5-minute interval component to refresh data
    )
    def update_graph(start_date, end_date, n_intervals):
        """
        Main callback function: loads data, filters by date, calculates stats,
        and updates the graph and all stat cards.
        """
        # Data Loading & Caching
        # Retrieve the database file's modification time for the cache invalidation key.
        mtime = get_db_mtime()
        # Load the cached or fresh data from the database using the mtime as the cache key.
        df = load_data(mtime, cache)

        # Check for absolutely no data
        if df.empty:
            return _get_empty_state_outputs(df, start_date, end_date)
        
        # Determine the actual date range to be used, including default handling
        min_date_available, max_date_available, new_start_date, new_end_date = _determine_date_range(df, start_date, end_date)

        # Filter the main DataFrame based on the determined dates
        date_filtered = _filter_dataframe_by_dates(df, new_start_date, new_end_date)

        # Calculate statistics for the displayed range
        average_price_display, highest_price_display, lowest_price_display = _calculate_range_stats(date_filtered)
        
        # Calculate Metadata for Display (using the *full* dataset for current price/update time)
        # Get the latest update time string
        last_updated_time_str = df["datetime"].max().strftime("%Y-%m-%d %H:%M:%S")
        last_updated_text = f"Last updated: {last_updated_time_str}"
        # Get the latest price (last row of the full dataframe)
        current_price_display = f"{df["price_gold"].iloc[-1]:,}"
        
        # Get the latest price change values
        latest_abs_change = df.iloc[-1]["price_change_abs"]
        latest_pct_change = df.iloc[-1]["price_change_pct"]
        # Format the change indicators
        price_change_indicators_display = _format_price_change_indicators(latest_abs_change, latest_pct_change)

        # No Data in Range Check (If the filtering resulted in an empty set)
        if date_filtered.empty:
            default_figure = {"data": [], "layout": {"title": {"text": "No Data Available", "x": 0.5}}}
            return (
                default_figure,
                min_date_available, max_date_available, new_start_date, new_end_date,
                last_updated_text,
                current_price_display,
                average_price_display,
                highest_price_display,
                lowest_price_display,
                price_change_indicators_display
            )

        # Generate Plot and Return
        line_figure = create_token_line_plot(date_filtered)

        # Return the figure and the updated date picker/stat card properties.
        return (
            line_figure, 
            min_date_available, max_date_available, new_start_date, new_end_date, 
            last_updated_text, 
            current_price_display, 
            average_price_display, 
            highest_price_display, 
            lowest_price_display,
            price_change_indicators_display
            )