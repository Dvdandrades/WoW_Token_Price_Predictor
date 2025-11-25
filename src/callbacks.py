from dash import Input, Output, html
import pandas as pd
from data_handler import get_db_mtime, load_data
from figures import create_token_line_plot
from config import COLOR_INCREASE, COLOR_DECREASE


def _filter_dataframe_by_days(df: pd.DataFrame, days_filter: int) -> pd.DataFrame:
    """
    Filters the DataFrame to include only rows within the last 'days_filter' days
    relative to the most recent timestamp in the data.

    Args:
        df: The input DataFrame containing 'datetime' column.
        days_filter: The number of days to look back.

    Returns:
        The filtered DataFrame.
    """
    if days_filter == 0 or df.empty:
        return df

    # Ensure 'datetime' is in datetime format before filtering
    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        df["datetime"] = pd.to_datetime(df["datetime"])

    # Calculate the start time for the filter window
    start_time = df["datetime"].max() - pd.Timedelta(days=days_filter)
    return df[df["datetime"] >= start_time]


def _format_price_change_indicators(
    latest_abs_change: float, latest_pct_change: float
) -> list[html.Span] | html.Span:
    """
    Formats the absolute and percentage price change into colored HTML `Span` elements
    for display in the dashboard's stat card.

    Args:
        latest_abs_change: The latest absolute change in price.
        latest_pct_change: The latest percentage change in price.

    Returns:
        A list of `html.Span` objects or a single "N/A" `html.Span`.
    """
    if pd.isna(latest_abs_change) or latest_abs_change is None:
        return html.Span("Change: N/A", style={"color": "gray"})

    is_positive = latest_abs_change >= 0
    # Use pre-configured colors based on the change direction
    color = COLOR_INCREASE if is_positive else COLOR_DECREASE
    sign = "+" if is_positive else ""

    # Return a list of two spans for absolute and percentage change
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


def register_callbacks(app, cache):
    """
    Registers all application callbacks with the Dash app instance.

    Args:
        app: The main Dash application instance.
        cache: The Flask-Caching instance for data caching.
    """

    @app.callback(
        Output("token-data-store", "data"),
        [
            Input("interval-check", "n_intervals"),
            Input("region-selector-dropdown", "value"),
        ],
    )
    def update_data_store(n_intervals, region):
        """
        Loads data from the DB using the cache and stores it as a list of dictionaries
        in the dcc.Store component for other callbacks to consume.

        The callback is triggered by a time interval or a region change.

        Args:
            n_intervals: The number of times the interval component has fired.
            region: The currently selected region identifier.

        Returns:
            The DataFrame's records as a list of dicts.
        """
        # Get the database modification time to use as a cache key
        mtime = get_db_mtime()
        # Load the data for the selected region, utilizing the cache
        df = load_data(mtime, cache, region)

        # Convert the DataFrame to a format suitable for the dcc.Store component
        return df.to_dict("records")

    @app.callback(
        Output("token-line-plot", "figure"),
        [Input("token-data-store", "data"), Input("days-filter-dropdown", "value")],
    )
    def update_graph(data, days_filter):
        """
        Reads data from the dcc.Store, applies the day filter, and generates
        the Plotly line chart.

        Args:
            data: The token price data as a list of dicts from the dcc.Store.
            days_filter: The number of days to display in the plot.

        Returns:
            The Plotly Figure object.
        """
        if not data:
            # Return a placeholder figure while waiting for data
            return {
                "data": [],
                "layout": {"title": {"text": "Waiting data...", "x": 0.5}},
            }

        df = pd.DataFrame(data)
        df["datetime"] = pd.to_datetime(df["datetime"])

        df_filtered = _filter_dataframe_by_days(df, days_filter)

        return create_token_line_plot(df_filtered)

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
        """
        Calculates and updates the main statistical indicators based on the filtered dataset.

        Args:
            data: The token price data as a list of dicts from the dcc.Store.
            days_filter: The number of days to use for average/min/max calculation.

        Returns:
            A tuple of strings/html.Span objects for the statistical output components.
        """
        na_values = ("N/A", "N/A", "N/A", "N/A", "N/A", html.Span("N/A"))

        if not data:
            return na_values

        df = pd.DataFrame(data)
        df["datetime"] = pd.to_datetime(df["datetime"])

        if df.empty:
            return na_values

        # Get latest record for current price, last update time, and indicators
        last_row = df.iloc[-1]
        last_updated_text = (
            f"Last updated: {last_row['datetime'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        # Format current price with comma as thousands separator
        current_price = f"{last_row['price_gold']:,}"

        # Format price change indicators using the helper function
        indicators = _format_price_change_indicators(
            last_row.get("price_change_abs"), last_row.get("price_change_pct")
        )

        # Filter the DataFrame for average, min, and max calculations
        df_filtered = _filter_dataframe_by_days(df, days_filter)

        if df_filtered.empty:
            # If filtering results in an empty set, return current data but N/A for range stats
            return (last_updated_text, current_price, "N/A", "N/A", "N/A", indicators)

        # Calculate and format filtered statistics
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
