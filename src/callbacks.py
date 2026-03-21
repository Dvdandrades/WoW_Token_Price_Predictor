import logging
import pandas as pd
from dash import Input, Output, html

from config import COLOR_DECREASE, COLOR_INCREASE
from db_reader import get_db_mtime, load_data
from figures import create_token_line_plot

logger = logging.getLogger(__name__)


def _filter_dataframe_by_days(df: pd.DataFrame, days_filter: int) -> pd.DataFrame:
    """
    Return rows within the last *days_filter* days relative to the latest
    timestamp in the data.  Returns *df* unchanged when *days_filter* is 0
    or the frame is empty.

    Args:
        df: DataFrame with a 'datetime' column.
        days_filter: Number of days to look back. 0 means no filter.
    """
    if days_filter == 0 or df.empty:
        return df

    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        df["datetime"] = pd.to_datetime(df["datetime"])

    start_time = df["datetime"].max() - pd.Timedelta(days=days_filter)
    return df[df["datetime"] >= start_time]


def _format_price_change_indicators(
    latest_abs_change: float, latest_pct_change: float
) -> list[html.Span] | html.Span:
    """
    Return a list of styled Span elements showing the absolute and percentage
    price change, or a single grey 'N/A' Span when the change is unavailable.

    Args:
        latest_abs_change: Absolute price change in gold.
        latest_pct_change: Percentage price change.
    """
    if pd.isna(latest_abs_change):
        return html.Span("Change: N/A", style={"color": "gray"})

    is_positive = latest_abs_change >= 0
    color = COLOR_INCREASE if is_positive else COLOR_DECREASE
    sign = "+" if is_positive else ""

    return [
        html.Span(
            f"{sign}{round(latest_abs_change):,} Gold",
            style={"color": color, "fontWeight": "bold", "marginRight": "10px"},
        ),
        html.Span(
            f"({sign}{latest_pct_change:.2f}%)",
            style={"color": color, "fontStyle": "italic"},
        ),
    ]


def register_callbacks(app, cache) -> None:
    """
    Register all Dash callbacks with *app*, injecting *cache* via closure.

    Args:
        app: Dash application instance.
        cache: Flask-Caching instance.
    """

    @app.callback(
        Output("token-data-store", "data"),
        [
            Input("interval-check", "n_intervals"),
            Input("region-selector-dropdown", "value"),
        ],
    )
    def update_data_store(n_intervals, region):
        mtime = get_db_mtime()
        df = load_data(mtime, cache, region)
        return df.to_dict("records")

    @app.callback(
        Output("token-line-plot", "figure"),
        [Input("token-data-store", "data"), Input("days-filter-dropdown", "value")],
    )
    def update_graph(data, days_filter):
        if not data:
            return {
                "data": [],
                "layout": {"title": {"text": "Waiting for data...", "x": 0.5}},
            }

        df = pd.DataFrame(data)
        df["datetime"] = pd.to_datetime(df["datetime"])
        return create_token_line_plot(_filter_dataframe_by_days(df, days_filter))

    @app.callback(
        [
            Output("last-updated-time", "children"),
            Output("current-price-value", "children"),
            Output("average-price-value", "children"),
            Output("highest-price-value", "children"),
            Output("lowest-price-value", "children"),
            Output("price_change_indicators", "children"),
        ],
        [Input("token-data-store", "data"), Input("days-filter-dropdown", "value")],
    )
    def update_stats(data, days_filter):
        na_values = ("N/A", "N/A", "N/A", "N/A", "N/A", html.Span("N/A"))

        if not data:
            return na_values

        df = pd.DataFrame(data)
        df["datetime"] = pd.to_datetime(df["datetime"])

        if df.empty:
            return na_values

        last_row = df.iloc[-1]
        last_updated_text = (
            f"Last updated: {last_row['datetime'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        current_price = f"{last_row['price_gold']:,}"
        indicators = _format_price_change_indicators(
            last_row.get("price_change_abs"), last_row.get("price_change_pct")
        )

        df_filtered = _filter_dataframe_by_days(df, days_filter)

        if df_filtered.empty:
            return (last_updated_text, current_price, "N/A", "N/A", "N/A", indicators)

        avg_price = f"{round(df_filtered['price_gold'].mean()):,}"
        max_price = f"{df_filtered['price_gold'].max():,}"
        min_price = f"{df_filtered['price_gold'].min():,}"

        return (
            last_updated_text,
            current_price,
            avg_price,
            max_price,
            min_price,
            indicators,
        )
