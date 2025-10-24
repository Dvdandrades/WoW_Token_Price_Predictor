import pandas as pd
import time
from dash import Dash, dcc, html, Input, Output
from pathlib import Path
from flask_caching import Cache

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = Path(__file__).parent.parent / "data" / "wow_token_prices.csv"
ASSET_PATH = PROJECT_ROOT / "assets"

# Dash App Configuration and Styling
# External stylesheet: Google Fonts (Lato)
external_stylesheet = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?"
            "family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet"
    },
]

# Initialize the Dash app with external styles and assets
app = Dash(__name__, assets_folder=ASSET_PATH, external_stylesheets=external_stylesheet)
app.title = "WoW Token Price"  # Title shown in browser tab

cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})

@cache.memoize(timeout=60 * 5)
def load_data(mtime):
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=["datetime", "price_gold"])
    
    df = pd.read_csv(
        DATA_PATH, 
        parse_dates=["datetime"],
        names=["datetime", "price_gold"], 
        # Add a check to ensure the header is explicitly read from the first row
        header=0,
        dtype={"price_gold": int}
    ).sort_values(by="datetime")

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_localize(None)
    return df

# App Layout Definition
app.layout = html.Div(
    children=[
        # Header Section: Title, Emoji, and Description
        html.Div(
            children=[
                html.P(children="🪙", className="header-emoji"),
                html.H1(children="WoW Token Price", className="header-title"),
                html.P(
                    children=(
                        "An interactive analysis of World of Warcraft "
                        "Token Price over time"
                    ),
                    className="header-description",
                ),
            ],
            className="header",
        ),

        # Menu Section: User Filters (Date Range)
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Date", className="menu-title"),
                        # DatePickerRange allows user to select a date window
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
        
        # Visualization Section: Graph Container
        html.Div(
            children=[
                # Line Chart Card
                html.Div(
                    children=dcc.Graph(
                        id="token-line-plot",
                        config={"displayModeBar": False},  # hides extra Plotly UI
                    ),
                    className="card",
                ),
                dcc.Interval(id="interval-check", interval=20 * 60 * 1000, n_intervals=0),
            ],
            className="wrapper",
        ),
    ]
)

# Callback: Update Graph Based on User Input
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
    Update the token price line chart based on the selected date range.

    Parameters
    ----------
    start_date : str
        The start date of the selected date range from the date picker.
    end_date : str
        The end date of the selected date range from the date picker.

    Returns
    -------
    dict
        A Plotly-compatible figure dictionary containing:
            - 'data': the line chart trace(s)
            - 'layout': chart appearance configuration
    """
    try:
        mtime = DATA_PATH.stat().st_mtime
    except FileNotFoundError:
        mtime = time.time()

    df = load_data(mtime)

    if df.empty:
        return (
            {"data": [], "layout": {"title": {"text": "No Data Available", "x": 0.5}}},
            None, None, None, None
        )

    min_date = df["datetime"].min().date().isoformat()
    max_date = df["datetime"].max().date().isoformat()
    new_start_date = start_date or min_date
    new_end_date = end_date or max_date

    start_dt = pd.to_datetime(new_start_date)
    end_dt = pd.to_datetime(new_end_date) + pd.Timedelta(days=1)

    date_filtered = df[
        (df["datetime"] >= start_dt) & 
        (df["datetime"] < end_dt)
    ]

    if date_filtered.empty:
         return (
            {"data": [], "layout": {"title": {"text": "No Data Available for Selected Range", "x": 0.5}}},
            min_date, max_date, new_start_date, new_end_date
        )

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
