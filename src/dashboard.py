import pandas as pd
from dash import Dash, dcc, html, Input, Output
from pathlib import Path



# Load and prepare dataset
data = (
    pd.read_csv(Path(__file__).parent.parent / "data" / "wow_token_prices.csv",
                parse_dates=["datetime"])
    .sort_values(by="datetime")
)

data["datetime"] = pd.to_datetime(data["datetime"], utc=True).dt.tz_localize(None)


# App configuration and styling
external_stylesheet = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?"
            "family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet"
    },
]

assets_path = Path(__file__).parent.parent / "assets"

# Initialize the Dash app
app = Dash(__name__, assets_folder= assets_path, external_stylesheets=external_stylesheet)
app.title = "WoW Token Price"

# Layout definition
app.layout = html.Div(
    children=[
        # Header section
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

        # Filter controls
        html.Div(
            children=[
                # Filter: Date range
                html.Div(
                    children=[
                        html.Div(children="Date", className="menu-title"),
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
        
        # Visualization cards
        html.Div(
            children=[
                # Line plot
                html.Div(
                    children=dcc.Graph(
                        id="token-line-plot",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)

# Callback : Update graph based on user filters
@app.callback(
    Output("token-line-plot", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def update_graph(start_date, end_date):
    # Filter data by date range
    date_filtered = data.query("(`datetime` >= @start_date) & (`datetime` <= @end_date)")

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
        "layout" : {
            "title": {"text": "WoW Token Price Over Time", "x": 0.05, "xanchor": "left"},
            "xaxis": {"title": "Date", "fixedrange": True},
            "yaxis": {"title": "Price in Gold", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }

    return line_figure

if __name__ == "__main__":
    app.run(debug=True)