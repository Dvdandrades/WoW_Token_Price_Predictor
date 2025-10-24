import pandas as pd
import time
from dash import Dash, dcc, html, Input, Output
from pathlib import Path
from flask_caching import Cache

# Path Configuration
# Define important project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = Path(__file__).parent.parent / "data" / "wow_token_prices.csv"
ASSET_PATH = PROJECT_ROOT / "assets"

# Dash App Configuration
# External stylesheet: Google Fonts (Lato)
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
# - `assets_folder` specifies the directory for CSS
# - `external_stylesheets` loads Google Fonts styling
app = Dash(__name__, assets_folder=ASSET_PATH, external_stylesheets=external_stylesheet)
app.title = "WoW Token Price"  # Browser tab title

# Enable simple in-memory caching for improved performance
cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})

# Data Loading Function
@cache.memoize(timeout=60 * 5)  # Cache data for 5 minutes
def load_data(mtime):
    """
    Load and preprocess the WoW token price data.

    Parameters
    ----------
    mtime : float
        Modification time of the CSV file used to invalidate cache.

    Returns
    -------
    pandas.DataFrame
        A sorted dataframe containing 'datetime' and 'price_gold' columns.
    """
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=["datetime", "price_gold"])

    # Read CSV with datetime parsing and explicit header handling
    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["datetime"],
        names=["datetime", "price_gold"],
        header=0,  # ensures the first row is treated as a header
        dtype={"price_gold": int},
    ).sort_values(by="datetime")

    # Normalize datetime
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_localize(None)
    return df

# App Layout
app.layout = html.Div(
    children=[
        # Header Section
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
            ],
            className="header",
        ),

        # Menu Section
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Date", className="menu-title"),
                        # Allows the user to select a date range
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

        # Visualization Section
        html.Div(
            children=[
                # Card container for the line chart
                html.Div(
                    children=dcc.Graph(
                        id="token-line-plot",
                        config={"displayModeBar": False},  # hides the Plotly toolbar
                    ),
                    className="card",
                ),
                # Interval component triggers periodic data refresh (every 20 minutes)
                dcc.Interval(id="interval-check", interval=20 * 60 * 1000, n_intervals=0),
            ],
            className="wrapper",
        ),
    ]
)

# Callback: Update Graph
@app.callback(
    Output("token-line-plot", "figure"),
    Output("date-range", "min_date_allowed"),
    Output("date-range", "max_date_allowed"),
    Output("date-range", "start_date"),
    Output("date-range", "end_date"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("interval-check", "n_intervals"),
)
def update_graph(start_date, end_date, n_intervals):
    """
    Update the line chart based on the selected date range and data refresh interval.

    Parameters
    ----------
    start_date : str
        Start date selected from the date picker.
    end_date : str
        End date selected from the date picker.
    n_intervals : int
        Counter that increments every interval (used to trigger data refresh).

    Returns
    -------
    tuple
        (figure, min_date, max_date, start_date, end_date)
    """
    # Retrieve the file's modification time for cache invalidation
    try:
        mtime = DATA_PATH.stat().st_mtime
    except FileNotFoundError:
        mtime = time.time()

    # Load the cached or fresh data
    df = load_data(mtime)

    # Handle case: no data available
    if df.empty:
        return (
            {"data": [], "layout": {"title": {"text": "No Data Available", "x": 0.5}}},
            None, None, None, None
        )

    # Establish the date range boundaries
    min_date = df["datetime"].min().date().isoformat()
    max_date = df["datetime"].max().date().isoformat()
    new_start_date = start_date or min_date
    new_end_date = end_date or max_date

    # Convert selected dates to datetime for filtering
    start_dt = pd.to_datetime(new_start_date)
    end_dt = pd.to_datetime(new_end_date) + pd.Timedelta(days=1)

    # Filter dataset by selected date range
    date_filtered = df[(df["datetime"] >= start_dt) & (df["datetime"] < end_dt)]

    # Handle case: no data within selected range
    if date_filtered.empty:
        return (
            {"data": [], "layout": {"title": {"text": "No Data Available for Selected Range", "x": 0.5}}},
            min_date, max_date, new_start_date, new_end_date
        )

    # Construct Plotly figure
    line_figure = {
        "data": [
            {
                "x": date_filtered["datetime"],
                "y": date_filtered["price_gold"],
                "type": "scatter",
                "mode": "lines+markers",
                "hovertemplate": (
                    "Date: %{x|%Y-%m-%d %H:%M:%S}<br>"
                    "Price: %{y} Gold<extra></extra>"
                ),
            },
        ],
        "layout": {
            "title": {"text": "WoW Token Price Over Time", "x": 0.05, "xanchor": "left"},
            "xaxis": {"title": "Date", "fixedrange": True},
            "yaxis": {"title": "Price in Gold", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }

    return line_figure, min_date, max_date, new_start_date, new_end_date
