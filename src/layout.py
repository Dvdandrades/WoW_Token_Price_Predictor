from dash import dcc, html

from config import DAYS_OPTIONS, DEFAULT_DAYS_FILTER, DEFAULT_REGION, REGION_OPTIONS


def create_layout() -> html.Div:
    """
    Build and return the root Div that forms the entire dashboard.

    Structure:
        - Header: title, subtitle, last-updated timestamp.
        - Stats cards: current price, average, high, low.
        - Controls: days filter + region selector dropdowns.
        - Graph: Plotly line chart with auto-refresh interval.
    """
    return html.Div(
        children=[
            # Header
            html.Div(
                children=[
                    dcc.Store(id="token-data-store", storage_type="memory"),
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
            # Statistics Card
            html.Div(
                children=[
                    # Current Price
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
                    # Average Price
                    html.Div(
                        children=[
                            html.H3(children="Average Price", className="card-title"),
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
                    # Highest Price
                    html.Div(
                        children=[
                            html.H3(children="Highest Price", className="card-title"),
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
                    # Lowest Price
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
            # Controls
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
            # Graph
            html.Div(
                children=[
                    html.Div(
                        children=dcc.Graph(
                            id="token-line-plot",
                            config={"displayModeBar": False},
                        ),
                        className="card",
                    ),
                    dcc.Interval(
                        id="interval-check",
                        interval=5 * 60 * 1000,  # 5 minutes in ms
                        n_intervals=0,
                    ),
                ],
                className="wrapper",
            ),
        ]
    )
