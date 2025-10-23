import pandas as pd
from dash import Dash, dcc, html, Input, Output
from pathlib import Path

# Data Loading and Preparation
# Read the WoW Token price dataset, ensure 'datetime' is parsed as a datetime,
# and sort chronologically to prepare for time series visualization.
data = (
    pd.read_csv(Path(__file__).parent.parent / "data" / "wow_token_prices.csv",
                parse_dates=["datetime"])
    .sort_values(by="datetime")
)

# Convert timezone-aware datetimes to naive for compatibility
data["datetime"] = pd.to_datetime(data["datetime"], utc=True).dt.tz_localize(None)

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

# Define the assets folder path for CSS.
assets_path = Path(__file__).parent.parent / "assets"

# Initialize the Dash app with external styles and assets
app = Dash(__name__, assets_folder=assets_path, external_stylesheets=external_stylesheet)
app.title = "WoW Token Price"  # Title shown in browser tab

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
                            min_date_allowed=data["datetime"].min().date(),
                            max_date_allowed=data["datetime"].max().date(),
                            start_date=data["datetime"].min().date(),
                            end_date=data["datetime"].max().date(),
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
            ],
            className="wrapper",
        ),
    ]
)

# Callback: Update Graph Based on User Input
@app.callback(
    Output("token-line-plot", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def update_graph(start_date, end_date):
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
    # Filter dataset by user-selected date range
    date_filtered = data.query("(`datetime` >= @start_date) & (`datetime` <= @end_date)")

    # Define figure for the line plot
    line_figure = {
        "data": [
            {
                "x": date_filtered["datetime"],
                "y": date_filtered["price_gold"],
                "type": "scatter",
                "mode": "lines+markers",
                "hovertemplate": (
                    "Date: %{x|%Y}<br>"
                    "Price: %{y}<extra></extra>"
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

    return line_figure

# Entry Point: Run the Dash Application
if __name__ == "__main__":
    # Run the Dash app in debug mode for live reloading and error display
    app.run(debug=True)
