from dash import dcc, html

from config import (
    CHART_HEATMAP,
    CHART_LINE,
    CHART_MULTIREGION,
    CHART_OHLC,
    DAYS_OPTIONS,
    DEFAULT_DAYS_FILTER,
    DEFAULT_REGION,
    REGION_OPTIONS,
)


def _stat_card(
    title: str,
    value_id: str,
    unit: str | None = "gold",
    extra_children: list | None = None,
) -> html.Div:
    """Helper that builds a single statistics card."""
    body: list = [
        html.H3(title, className="card-title"),
        html.P(id=value_id, children="N/A", className="card-value"),
    ]
    if unit:
        body.append(html.P(unit, className="card-unit"))
    if extra_children:
        body.extend(extra_children)
    return html.Div(body, className="stat-card")


def create_layout() -> html.Div:
    """
    Build and return the root Div that forms the entire dashboard.

    Structure
    ---------
    1. Persistent stores (theme, alert threshold, multi-region selection)
    2. Header  — title · subtitle · last-updated · dark-mode toggle · worker badge
    3. Alert banner  — conditionally visible
    4. Stats row  — current price (with percentile) · average · high · low
    5. Controls  — days filter · region selector · chart-type tabs
    6. Multi-region region picker  — visible only in "Compare Regions" tab
    7. Main chart
    8. Intervals  — data refresh · worker-status refresh
    """
    return html.Div(
        id="app-container",
        children=[
            # Persistent client-side stores
            dcc.Store(id="token-data-store", storage_type="memory"),
            dcc.Store(id="multi-region-data-store", storage_type="memory"),
            dcc.Store(id="theme-store", storage_type="local", data="light"),
            # Download target for CSV export
            dcc.Download(id="download-csv"),
            # Header
            html.Div(
                className="header",
                children=[
                    html.Div(
                        className="header-top-row",
                        children=[
                            html.Div(
                                children=[
                                    html.H1(
                                        "World Of Warcraft Token Price",
                                        className="header-title",
                                    ),
                                    html.P(
                                        "An interactive dashboard for exploring "
                                        "World of Warcraft token price trends over time.",
                                        className="header-description",
                                    ),
                                    html.P(
                                        id="last-updated-time",
                                        className="header-description header-timestamp",
                                    ),
                                ]
                            ),
                            html.Div(
                                className="header-controls",
                                children=[
                                    # Worker status badge
                                    html.Div(
                                        className="worker-badge",
                                        children=[
                                            html.Span("●", id="worker-status-dot"),
                                            html.Span(
                                                "Checking…",
                                                id="worker-status-text",
                                                className="worker-status-text",
                                            ),
                                        ],
                                    ),
                                    # Dark-mode toggle
                                    html.Button(
                                        "🌙 Dark",
                                        id="theme-toggle-btn",
                                        className="theme-toggle-btn",
                                        n_clicks=0,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            # Alert banner
            html.Div(id="alert-banner", className="alert-banner"),
            # Stats row
            html.Div(
                className="stats-container",
                children=[
                    # Current price card — includes price-change indicators and percentile
                    html.Div(
                        className="stat-card stat-card--primary",
                        children=[
                            html.H3("Current Price", className="card-title"),
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
                            html.P(
                                id="percentile-badge",
                                children="",
                                className="percentile-badge",
                            ),
                        ],
                    ),
                    _stat_card("Average Price", "average-price-value"),
                    _stat_card("Highest Price", "highest-price-value"),
                    _stat_card("Lowest Price", "lowest-price-value"),
                    # Alert threshold input — lives in a card for visual consistency
                    html.Div(
                        className="stat-card stat-card--alert",
                        children=[
                            html.H3("Price Alert", className="card-title"),
                            html.P(
                                "Notify when price reaches:",
                                className="card-unit",
                                style={"marginBottom": "8px"},
                            ),
                            dcc.Input(
                                id="alert-threshold-input",
                                type="number",
                                placeholder="Threshold (Gold)",
                                min=0,
                                debounce=True,
                                className="alert-threshold-input",
                            ),
                            html.P(
                                "gold",
                                className="card-unit",
                                style={"marginTop": "4px"},
                            ),
                        ],
                    ),
                ],
            ),
            # Controls
            html.Div(
                className="menu",
                children=[
                    html.Div(
                        children=[
                            html.Div("Filter by Days", className="menu-title"),
                            dcc.Dropdown(
                                id="days-filter-dropdown",
                                options=DAYS_OPTIONS,
                                value=DEFAULT_DAYS_FILTER,
                                clearable=False,
                                className="dash-dropdown",
                            ),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Div("Region", className="menu-title"),
                            dcc.Dropdown(
                                id="region-selector-dropdown",
                                options=REGION_OPTIONS,
                                value=DEFAULT_REGION,
                                clearable=False,
                                className="dash-dropdown",
                            ),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Div("Chart Type", className="menu-title"),
                            dcc.RadioItems(
                                id="chart-type-selector",
                                options=[
                                    {"label": "Price & EMA", "value": CHART_LINE},
                                    {"label": "Daily OHLC", "value": CHART_OHLC},
                                    {"label": "Heatmap", "value": CHART_HEATMAP},
                                    {
                                        "label": "Compare Regions",
                                        "value": CHART_MULTIREGION,
                                    },
                                ],
                                value=CHART_LINE,
                                className="chart-type-radio",
                                inline=True,
                            ),
                        ]
                    ),
                ],
            ),
            # Multi-region picker (shown only in "Compare Regions" mode)
            html.Div(
                id="multi-region-picker-container",
                className="multi-region-picker",
                style={"display": "none"},
                children=[
                    html.Div("Select regions to compare:", className="menu-title"),
                    dcc.Checklist(
                        id="multi-region-checklist",
                        options=REGION_OPTIONS,
                        value=["eu", "us"],
                        className="region-checklist",
                        inline=True,
                    ),
                ],
            ),
            # Main chart + export button
            html.Div(
                className="wrapper",
                children=[
                    html.Div(
                        className="chart-toolbar",
                        children=[
                            html.Button(
                                "⬇ Export CSV",
                                id="export-csv-btn",
                                className="export-btn",
                                n_clicks=0,
                            ),
                        ],
                    ),
                    html.Div(
                        className="card",
                        children=[
                            dcc.Graph(
                                id="token-line-plot",
                                config={"displayModeBar": False},
                            ),
                        ],
                    ),
                ],
            ),
            # Intervals
            dcc.Interval(
                id="interval-check",
                interval=5 * 60 * 1_000,  # 5 minutes
                n_intervals=0,
            ),
            dcc.Interval(
                id="worker-status-interval",
                interval=60 * 1_000,  # 1 minute
                n_intervals=0,
            ),
        ],
    )
