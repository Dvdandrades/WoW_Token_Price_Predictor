import pandas as pd
import time
from dash import Dash, dcc, html, Input, Output
from pathlib import Path
from flask_caching import Cache
import sqlite3
import os
import plotly.express as px
from data_manager import DB_PATH

# Path Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSET_PATH = PROJECT_ROOT / "assets"

# Dash App Configuration
# External stylesheet: Google Fonts (Lato) is loaded for styling.
external_stylesheet = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?"
            "family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
]

# Initialize the Dash application
# - `assets_folder` specifies the directory for local CSS/assets
# - `external_stylesheets` loads Google Fonts styling
app = Dash(__name__, assets_folder=ASSET_PATH, external_stylesheets=external_stylesheet)
app.title = "WoW Token Price"  # Browser tab title

# Enable simple in-memory caching for improved performance.
# Cache is attached to the Flask server instance within the Dash app.
cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})

def get_db_mtime():
    """Returns the modification time of the SQLite database file."""
    if DB_PATH.exists():
        return os.path.getmtime(DB_PATH)
    # Return current time if file doesn't exist, preventing cache issues on startup.
    return time.time()

# Data Loading Function
@cache.memoize(timeout=60 * 5)  # Cache data for 5 minutes
def load_data(mtime):
    """
    Load and preprocess the WoW token price data from the SQLite database.

    The 'mtime' parameter forces cache invalidation when the underlying database file changes.

    Parameters
    ----------
    mtime : float
        Modification time of the database file used to invalidate the cache.

    Returns
    -------
    pandas.DataFrame
        A sorted DataFrame containing 'datetime' (tz-naive) and 'price_gold' columns.
        Returns an empty DataFrame if the database file is not found or an error occurs.
    """
    if not DB_PATH.exists():
        # Log absence and return empty frame
        print(f"Database not found at {DB_PATH}. Returning empty DataFrame.")
        return pd.DataFrame(columns=["datetime", "price_gold"])

    try:
        conn = sqlite3.connect(DB_PATH)

        # Execute SQL query to get all sorted data
        df = pd.read_sql_query(
            "SELECT datetime, price_gold FROM token_prices ORDER BY datetime",
            conn
        )
        conn.close()

        # Data Preprocessing: Convert datetime and price to correct types
        df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize(None) # Remove timezone info
        df["price_gold"] = df["price_gold"].astype(int)
        return df
    except sqlite3.Error as e:
        print(f"SQLite Error during data loading: {e}")
        return pd.DataFrame(columns=["datetime", "price_gold"])

# App Layout Definition
app.layout = html.Div(
    children=[
        # Header Section: Contains title and description
        html.Div(
            children=[
                html.P(children="🪙", className="header-emoji"),
                html.H1(children="WoW Token Price", className="header-title"),
                html.P(
                    children=(
                        "An interactive dashboard for exploring "
                        "World of Warcraft token price trends over time."
                    ),
                    className="header-description",
                ),
                html.P(
                    id="last-updated-time",
                    className="header-description",
                    style={"fontStyle": "italic", "marginTop": "5px", "fontSize": "0.9em"},
                ),
            ],
            className="header",
        ),
        # Statistics Card Container
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.H3(children="Current Price", className="card-title"),
                        html.P(
                            id="current-price-value",
                            children="N/A",
                            className="card-value",
                        ),
                        html.P(
                            children="gold",
                            className="card-unit",
                        ),
                    ],
                    className="stat-card",
                ),
            ],
            className="stats-container",
        ),

        # Menu Section: Contains interactive filters
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Date Range Selection", className="menu-title"),
                        # DatePickerRange allows the user to select a date range
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=None,
                            max_date_allowed=None,
                        ),
                    ]
                ),
            ],
            className="menu",
        ),

        # Visualization Section: Holds the main line chart and the auto-refresh interval
        html.Div(
            children=[
                # Card container for the line chart
                html.Div(
                    children=dcc.Graph(
                        id="token-line-plot",
                        config={"displayModeBar": False},  # Hides the Plotly toolbar
                    ),
                    className="card",
                ),
                # Interval component triggers periodic data refresh (every 20 minutes)
                # This causes the callback to fire, which checks for new data via cache invalidation.
                dcc.Interval(id="interval-check", interval=5 * 60 * 1000, n_intervals=0),
            ],
            className="wrapper",
        ),
    ]
)

# Callback: Update Graph and Date Picker Limits
@app.callback(
    (
    Output("token-line-plot", "figure"),
    Output("date-range", "min_date_allowed"),
    Output("date-range", "max_date_allowed"),
    Output("date-range", "start_date"),
    Output("date-range", "end_date"),
    Output("last-updated-time", "children"),
    Output("current-price-value", "children"),
    ),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("interval-check", "n_intervals"),
)
def update_graph(start_date, end_date, n_intervals):
    """
    Updates the line chart and sets the allowed boundaries for the DatePickerRange.

    Data is refreshed every 'n_intervals' trigger (20 minutes) by checking the database
    modification time to bypass the `load_data` function's cache if needed.

    Parameters
    ----------
    start_date : str | None
        Start date selected by the user (or None if unselected).
    end_date : str | None
        End date selected by the user (or None if unselected).
    n_intervals : int
        Counter for the interval component, used to force a refresh check.

    Returns
    -------
    tuple
        (figure: dict, min_date: str, max_date: str, new_start_date: str, new_end_date: str)
        The Plotly figure dictionary and the updated date picker properties.
    """
    # Retrieve the file's modification time for cache invalidation key in load_data
    mtime = get_db_mtime()

    # Load the cached or fresh data based on mtime
    df = load_data(mtime)

    # Placeholder values for no-data state
    last_updated_text = "Last updated: N/A"
    current_price_display = "N/A"

    # Handle case: no data available
    if df.empty:
        # Return a placeholder figure and reset all date picker properties
        return (
            {"data": [], "layout": {"title": {"text": "No Data Available", "x": 0.5}}},
            None, None, None, None,
            last_updated_text,
            current_price_display
        )
    
    # Calculate the latest data time
    last_updated_time_str = df["datetime"].max().strftime("%Y-%m-%d %H:%M:%S")
    last_updated_text = f"Last updated: {last_updated_time_str}"

    # Get the most recent price for display
    current_price_display = f"{df["price_gold"].iloc[-1]:,}"

    # Establish the date range boundaries based on loaded data
    min_date = df["datetime"].min().date().isoformat()
    max_date = df["datetime"].max().date().isoformat()

    # Set default date range to the full extent of the data if no selection is made
    new_start_date = start_date or min_date
    new_end_date = end_date or max_date

    # Convert selected dates to datetime objects for filtering.
    # Add one day to the end date to include all data points up to the end of that day.
    start_dt = pd.to_datetime(new_start_date)
    end_dt = pd.to_datetime(new_end_date) + pd.Timedelta(days=1)

    # Filter dataset by selected date range
    date_filtered = df[(df["datetime"] >= start_dt) & (df["datetime"] < end_dt)]

    # Handle case: no data within selected range
    if date_filtered.empty:
        # Return a placeholder figure but keep the date boundaries and selections intact
        return (
            {"data": [], "layout": {"title": {"text": "No Data Available for Selected Range", "x": 0.5}}},
            min_date, max_date, new_start_date, new_end_date,
            last_updated_text,
            current_price_display
        )

    # Construct Plotly figure definition
    line_figure = px.line(
        date_filtered,
        x="datetime",
        y="price_gold",
        title="WoW Token Price Over Time",
    )

    line_figure.update_traces(
        mode="lines+markers",
        line_color="#17B897",
        hovertemplate=(
            "Date: %{x|%Y-%m-%d %H:%M:%S}<br>"
            "Price: %{y} Oro<extra></extra>"
        ),
    )

    line_figure.update_layout(
        title_x=0.05,
        title_xanchor="left",
        xaxis_title="Date",
        yaxis_title="Price (Godl)",
        xaxis_fixedrange=True,
        yaxis_fixedrange=True,
    )

    # Return the figure and the updated date picker properties
    return line_figure, min_date, max_date, new_start_date, new_end_date, last_updated_text, current_price_display
