from __future__ import annotations
import logging
import time
import pandas as pd

from dash import Input, Output, html, State, no_update


from config import (
    CHART_HEATMAP,
    CHART_MULTIREGION,
    CHART_OHLC,
    COLOR_DECREASE,
    COLOR_INCREASE,
    OHLC_MIN_DAYS,
    REGION_OPTIONS,
    get_settings,
)
from db_reader import (
    build_heatmap_pivot,
    build_ohlc_data,
    get_db_mtime,
    get_price_percentile,
    load_data,
    load_data_multi_region,
    maybe_downsample,
)
from figures import (
    create_heatmap_figure,
    create_multi_region_plot,
    create_ohlc_chart,
    create_token_line_plot,
)

logger = logging.getLogger(__name__)


# Internal helpers
def _filter_by_days(df: pd.DataFrame, days_filter: int) -> pd.DataFrame:
    """
    Return rows within the last *days_filter* days relative to the latest
    timestamp in the data. Returns *df* unchanged when *days_filter* is 0
    or the frame is empty.

    Args:
        df: DataFrame with a 'datetime' column.
        days_filter: Number of days to look back. 0 means no filter.
    """
    if days_filter == 0 or df.empty:
        return df

    if not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
        df = df.copy()
        df["datetime"] = pd.to_datetime(df["datetime"])

    start = df["datetime"].max() - pd.Timedelta(days=days_filter)
    return df[df["datetime"] >= start]


def _price_change_spans(
    abs_change: float, pct_change: float
) -> list[html.Span] | html.Span:
    """Return styled Span elements for the price-change row, or 'N/A'."""
    if pd.isna(abs_change):
        return html.Span("Change: N/A", style={"color": "gray"})

    positive = abs_change >= 0
    color = COLOR_INCREASE if positive else COLOR_DECREASE
    sign = "+" if positive else ""

    return [
        html.Span(
            f"{sign}{round(abs_change):,} Gold",
            style={"color": color, "fontWeight": "bold", "marginRight": "10px"},
        ),
        html.Span(
            f"({sign}{pct_change:.2f}%)",
            style={"color": color, "fontStyle": "italic"},
        ),
    ]


def _percentile_content(percentile: float | None) -> tuple[str, dict]:
    """Return (label_text, style) for the percentile badge."""
    if percentile is None:
        return "Percentile: N/A", {"color": "gray"}

    # Low percentile = price is cheap relative to history → good time to buy
    color = (
        COLOR_INCREASE
        if percentile <= 40
        else (COLOR_DECREASE if percentile >= 70 else "#F5A623")
    )
    label = f"{percentile:.0f}th percentile (30d)"
    hint = " ← buy?" if percentile <= 30 else (" ← sell?" if percentile >= 80 else "")
    return f"{label}{hint}", {"color": color, "fontSize": "0.82em", "marginTop": "4px"}


# Registration
def register_callbacks(app, cache) -> None:
    """
    Register all Dash callbacks with *app*, injecting *cache* via closure.

    Args:
        app: Dash application instance.
        cache: Flask-Caching instance.
    """

    # Data store - single region
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

    # Data store - multi-region
    @app.callback(
        Output("multi-region-data-store", "data"),
        [
            Input("interval-check", "n_intervals"),
            Input("chart-type-selector", "value"),
            Input("multi-region-checklist", "value"),
            Input("days-filter-dropdown", "value"),
        ],
    )
    def update_multi_region_store(
        n_intervals, chart_type, selected_regions, days_filter
    ):
        if chart_type != CHART_MULTIREGION:
            return no_update

        regions = selected_regions or [opt["value"] for opt in REGION_OPTIONS]
        mtime = get_db_mtime()
        dfs = load_data_multi_region(mtime, cache, regions)

        result = {}
        for region, df in dfs.items():
            df = _filter_by_days(df, days_filter)
            df = maybe_downsample(df)
            result[region] = df.to_dict("records")
        return result

    # Main chart dispatch
    @app.callback(
        Output("token-line-plot", "figure"),
        [
            Input("token-data-store", "data"),
            Input("multi-region-data-store", "data"),
            Input("days-filter-dropdown", "value"),
            Input("chart-type-selector", "value"),
            Input("theme-store", "data"),
        ],
    )
    def update_graph(data, multi_data, days_filter, chart_type, theme):
        dark = theme == "dark"

        if chart_type == CHART_MULTIREGION:
            if not multi_data:
                return create_multi_region_plot({}, dark_mode=dark)
            dfs = {
                region: pd.DataFrame(records).pipe(
                    lambda df: df.assign(datetime=pd.to_datetime(df["datetime"]))
                    if not df.empty
                    else df
                )
                for region, records in multi_data.items()
            }
            return create_multi_region_plot(dfs, dark_mode=dark)

        # All other chart types need the single-region DataFrame
        if not data:
            return create_token_line_plot(pd.DataFrame(), dark_mode=dark)

        df = pd.DataFrame(data)
        if df.empty:
            return create_token_line_plot(df, dark_mode=dark)

        df["datetime"] = pd.to_datetime(df["datetime"])

        if chart_type == CHART_OHLC:
            filtered = _filter_by_days(df, days_filter)
            ohlc = build_ohlc_data(filtered)
            # Require at least OHLC_MIN_DAYS distinct days
            if ohlc.empty or len(ohlc) < OHLC_MIN_DAYS:
                return create_ohlc_chart(pd.DataFrame(), dark_mode=dark)
            return create_ohlc_chart(ohlc, dark_mode=dark)

        if chart_type == CHART_HEATMAP:
            # Heatmap uses all historical data (ignore days filter) for
            # a statistically meaningful day/hour distribution
            pivot = build_heatmap_pivot(df)
            return create_heatmap_figure(pivot, dark_mode=dark)

        # Default: LINE chart
        filtered = _filter_by_days(df, days_filter)
        sampled = maybe_downsample(filtered)
        return create_token_line_plot(
            sampled,
            ema_span_days=get_settings().ema_span_days,
            dark_mode=dark,
        )

    # Stats panel
    @app.callback(
        [
            Output("last-updated-time", "children"),
            Output("current-price-value", "children"),
            Output("average-price-value", "children"),
            Output("highest-price-value", "children"),
            Output("lowest-price-value", "children"),
            Output("price_change_indicators", "children"),
            Output("percentile-badge", "children"),
            Output("percentile-badge", "style"),
        ],
        [
            Input("token-data-store", "data"),
            Input("days-filter-dropdown", "value"),
        ],
    )
    def update_stats(data, days_filter):
        na_pct_style = {"color": "gray"}
        na_values = (
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            html.Span("N/A"),
            "Percentile: N/A",
            na_pct_style,
        )

        if not data:
            return na_values

        df = pd.DataFrame(data)
        if df.empty:
            return na_values

        df["datetime"] = pd.to_datetime(df["datetime"])
        last_row = df.iloc[-1]

        last_updated = (
            f"Last updated: {last_row['datetime'].strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        current_price_str = f"{int(last_row['price_gold']):,}"
        indicators = _price_change_spans(
            last_row.get("price_change_abs"), last_row.get("price_change_pct")
        )

        # Percentile uses full history (all rows), not the filtered window
        percentile = get_price_percentile(last_row["price_gold"], df)
        pct_text, pct_style = _percentile_content(percentile)

        # Filtered window for avg / max / min
        df_filtered = _filter_by_days(df, days_filter)
        if df_filtered.empty:
            return (
                last_updated,
                current_price_str,
                "N/A",
                "N/A",
                "N/A",
                indicators,
                pct_text,
                pct_style,
            )

        avg = f"{round(df_filtered['price_gold'].mean()):,}"
        high = f"{int(df_filtered['price_gold'].max()):,}"
        low = f"{int(df_filtered['price_gold'].min()):,}"

        return (
            last_updated,
            current_price_str,
            avg,
            high,
            low,
            indicators,
            pct_text,
            pct_style,
        )

    # Price alert banner
    @app.callback(
        [
            Output("alert-banner", "children"),
            Output("alert-banner", "className"),
        ],
        [
            Input("token-data-store", "data"),
            Input("alert-threshold-input", "value"),
        ],
    )
    def update_alert_banner(data, threshold):
        hidden = ("", "alert-banner")

        if not data or not threshold or threshold <= 0:
            return hidden

        df = pd.DataFrame(data)
        if df.empty:
            return hidden

        current = int(df.iloc[-1]["price_gold"])

        if current <= threshold:
            msg = f"🔔 Price Alert!  Current price ({current:,} Gold) is at or below your threshold ({int(threshold):,} Gold)."
            return msg, "alert-banner alert-banner--below"
        elif current >= threshold * 1.05:
            msg = f"📈 Price is above threshold.  Current: {current:,} Gold  (threshold: {int(threshold):,} Gold)."
            return msg, "alert-banner alert-banner--above"
        else:
            msg = f"⚠️ Price approaching threshold.  Current: {current:,} Gold  (threshold: {int(threshold):,} Gold)."
            return msg, "alert-banner alert-banner--near"

    # Worker status badge
    @app.callback(
        [
            Output("worker-status-text", "children"),
            Output("worker-status-dot", "style"),
        ],
        Input("worker-status-interval", "n_intervals"),
    )
    def update_worker_status(_n):
        mtime = get_db_mtime()
        elapsed = time.time() - mtime
        minutes_ago = int(elapsed / 60)
        threshold = get_settings().worker_interval_minutes * 60 * 1.5

        if elapsed < threshold:
            dot_style = {
                "color": COLOR_INCREASE,
                "fontSize": "0.9em",
                "marginRight": "5px",
            }
            label = f"Worker active · {minutes_ago}m ago"
        else:
            dot_style = {
                "color": COLOR_DECREASE,
                "fontSize": "0.9em",
                "marginRight": "5px",
            }
            label = f"Worker stale · {minutes_ago}m ago"

        return label, dot_style

    # Dark-mode toggle
    @app.callback(
        [
            Output("theme-store", "data"),
            Output("theme-toggle-btn", "children"),
            Output("app-container", "className"),
        ],
        Input("theme-toggle-btn", "n_clicks"),
        State("theme-store", "data"),
    )
    def toggle_dark_mode(n_clicks, current_theme):
        if n_clicks and n_clicks % 2 == 1:
            return "dark", "☀️ Light", "dark"
        return "light", "🌙 Dark", ""

    # Show / hide multi-region picker
    @app.callback(
        Output("multi-region-picker-container", "style"),
        Input("chart-type-selector", "value"),
    )
    def toggle_multi_region_picker(chart_type):
        if chart_type == CHART_MULTIREGION:
            return {"display": "flex", "alignItems": "center", "gap": "16px"}
        return {"display": "none"}

    # CSV export
    @app.callback(
        Output("download-csv", "data"),
        Input("export-csv-btn", "n_clicks"),
        [
            State("token-data-store", "data"),
            State("days-filter-dropdown", "value"),
            State("region-selector-dropdown", "value"),
        ],
        prevent_initial_call=True,
    )
    def export_csv(n_clicks, data, days_filter, region):
        if not n_clicks or not data:
            return no_update

        df = pd.DataFrame(data)
        if df.empty:
            return no_update

        df["datetime"] = pd.to_datetime(df["datetime"])
        filtered = _filter_by_days(df, days_filter)

        days_label = f"{days_filter}d" if days_filter > 0 else "all"
        filename = f"wow_token_{region}_{days_label}.csv"

        return {"content": filtered.to_csv(index=False), "filename": filename}
