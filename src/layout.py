from dash import dcc, html

def create_layout():
    """Defines the overall layout of the Dash application."""
    return html.Div(
        children=[
            # Header Section (Title and Description)
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
                    )
                ],
                className="stats-container",
            ),

            # Menu Section (Date Range Picker)
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.Div(children="Date Range Selection", className="menu-title"),
                            dcc.DatePickerRange(
                                id="date-range",
                                # min/max dates are set dynamically by the callback
                                min_date_allowed=None,
                                max_date_allowed=None,
                            ),
                        ]
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
                    dcc.Interval(id="interval-check", interval=5 * 60 * 1000, n_intervals=0),
                ],
                className="wrapper",
            ),
        ]
    )