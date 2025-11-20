from dash import dcc, html
from config import DAYS_OPTIONS, DEFAULT_DAYS_FILTER, REGION_OPTIONS, DEFAULT_REGION


def create_layout() -> html.Div:
    """Defines the overall layout of the Dash application."""
    return html.Div(
        children=[
            # Header Section (Title and Description)
            html.Div(
                children=[
                    html.H1(
                        children="World Of Warcraft Token Price",
                        className="header-title",
                    ),
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
                        style={
                            "fontStyle": "italic",
                            "marginTop": "5px",
                            "fontSize": "0.9em",
                        },
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
                                id="price_change_indicators",
                                children="N/A",
                                className="card-indicator",
                            ),
                        ],
                        className="stat-card",
                    ),
                    html.Div(
                        children=[
                            html.H3(children=("Average Price"), className="card-title"),
                            html.P(
                                id="average-price-value",
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
                    html.Div(
                        children=[
                            html.H3(children=("Highest Price"), className="card-title"),
                            html.P(
                                id="highest-price-value",
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
                    html.Div(
                        children=[
                            html.H3(children=("Lowest Price"), className="card-title"),
                            html.P(
                                id="lowest-price-value",
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
            # Menu Section (Date Range Picker and Dropdowns)
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.Div(children="Filter by Days", className="menu-title"),
                            dcc.Dropdown(
                                id="days-filter-dropdown",
                                options=DAYS_OPTIONS,
                                value=DEFAULT_DAYS_FILTER,
                                clearable=False,
                                className="dash-dropdown",
                            ),
                        ],
                    ),
                    html.Div(
                        children=[
                            html.Div(
                                children="Region Selection", className="menu-title"
                            ),
                            dcc.Dropdown(
                                id="region-selector-dropdown",
                                options=REGION_OPTIONS,
                                value=DEFAULT_REGION,
                                clearable=False,
                                className="dash-dropdown",
                            ),
                        ],
                    ),
                ],
                className="menu",
            ),
            # Visualization Section (Line Chart and Interval)
            html.Div(
                children=[
                    # Line Chart Card
                    html.Div(
                        children=dcc.Graph(
                            id="token-line-plot",
                            config={"displayModeBar": False},
                        ),
                        className="card",
                    ),
                    # Auto-refresh interval (5 minutes) to trigger data reload/update
                    dcc.Interval(
                        id="interval-check", interval=5 * 60 * 1000, n_intervals=0
                    ),
                ],
                className="wrapper",
            ),
        ]
    )
