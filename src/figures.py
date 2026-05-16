from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd

from config import COLOR_DECREASE, COLOR_INCREASE, REGION_COLORS

# Theme helpers
_LIGHT = {
    "bg": "#ffffff",
    "paper": "#ffffff",
    "font": "#4b5563",
    "grid": "#e5e7eb",
    "axis_line": "#d1d5db",
}

_DARK = {
    "bg": "#0f172a",
    "paper": "#1e293b",
    "font": "#e2e8f0",
    "grid": "#334155",
    "axis_line": "#475569",
}


def _t(dark_mode: bool) -> dict:
    return _DARK if dark_mode else _LIGHT


def _base_layout(
    title: str,
    x_title: str,
    y_title: str,
    dark_mode: bool,
    extra_margin: dict | None = None,
) -> dict:
    """Return a shared layout dict with consistent theming."""
    theme = _t(dark_mode)
    margin = dict(l=50, r=20, t=55, b=45)
    if extra_margin:
        margin.update(extra_margin)

    return dict(
        title={"text": title, "x": 0.05, "xanchor": "left", "font": {"size": 15}},
        xaxis_title=x_title,
        yaxis_title=y_title,
        xaxis=dict(
            gridcolor=theme["grid"],
            showgrid=True,
            fixedrange=True,
            linecolor=theme["axis_line"],
            tickfont=dict(color=theme["font"]),
            title_font=dict(color=theme["font"]),
        ),
        yaxis=dict(
            gridcolor=theme["grid"],
            showgrid=True,
            fixedrange=True,
            linecolor=theme["axis_line"],
            tickfont=dict(color=theme["font"]),
            title_font=dict(color=theme["font"]),
            tickformat=",d",
        ),
        hovermode="x unified",
        margin=margin,
        plot_bgcolor=theme["bg"],
        paper_bgcolor=theme["paper"],
        font={"color": theme["font"]},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=theme["font"]),
        ),
    )


def _empty_fig(message: str, dark_mode: bool) -> go.Figure:
    theme = _t(dark_mode)
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor=theme["bg"],
        paper_bgcolor=theme["paper"],
        font={"color": theme["font"]},
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text=message,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color=theme["font"]),
            )
        ],
    )
    return fig


# Public figure factories
def create_token_line_plot(
    df: pd.DataFrame, ema_span_days: int = 7, dark_mode: bool = False
) -> go.Figure:
    """
    Dual-line chart (actual price + EMA) with a rolling standard-deviation
    band drawn around the EMA for volatility context.

    Args:
        df: Pre-filtered DataFrame with 'datetime', 'price_gold', and 'ema'.
        ema_span_days: Label used in the EMA legend entry.
        dark_mode: When True, apply the dark colour theme.
    """
    if df.empty:
        return _empty_fig("Waiting for data…", dark_mode)

    fig = go.Figure()

    # Adaptive rolling window for the std band (roughly 10 % of visible data,
    # at least 3 points so the std is meaningful).
    window = max(3, len(df) // 10)
    rolling_std = df["price_gold"].rolling(window=window, min_periods=1).std().fillna(0)
    upper = df["ema"] + rolling_std
    lower = df["ema"] - rolling_std

    # Standard-deviation band: two invisible boundary traces with fill between them
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=upper,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
            name="_upper_band",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=lower,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(255, 99, 71, 0.10)",
            name="±1σ Band",
            hoverinfo="skip",
        )
    )

    # Actual price line
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["price_gold"],
            mode="lines",
            line=dict(color=COLOR_INCREASE, width=2),
            name="Actual Price",
            hovertemplate="Date: %{x|%Y-%m-%d %H:%M:%S}<br>Price: %{y} Gold<extra></extra>",
        )
    )

    # EMA line
    ema_label = f"EMA ({ema_span_days}-day)"
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["ema"],
            mode="lines",
            line=dict(color=COLOR_DECREASE, width=2, dash="dash"),
            name=ema_label,
            hovertemplate=(
                f"Date: %{{x|%Y-%m-%d %H:%M:%S}}<br>EMA: %{{y}} Gold"
                f"<extra>{ema_label}</extra>"
            ),
        )
    )

    fig.update_layout(
        **_base_layout("WoW Token Price Over Time", "Date", "Price (Gold)", dark_mode)
    )
    return fig


def create_multi_region_plot(
    dfs: dict[str, pd.DataFrame], dark_mode: bool = False
) -> go.Figure:
    """
    Overlay one price line per region onto a single chart for direct comparison.

    Args:
        dfs: Mapping of region identifier → pre-filtered DataFrame.
        dark_mode: Dark colour theme flag.
    """
    if not dfs or all(v.empty for v in dfs.values()):
        return _empty_fig("No data available for selected regions.", dark_mode)

    fig = go.Figure()

    for region, df in dfs.items():
        if df.empty:
            continue
        color = REGION_COLORS.get(region, "#888888")
        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df["price_gold"],
                mode="lines",
                line=dict(color=color, width=2),
                name=region.upper(),
                hovertemplate=(
                    f"Date: %{{x|%Y-%m-%d %H:%M}}<br>"
                    f"{region.upper()}: %{{y:,.0f}} Gold<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        **_base_layout(
            "WoW Token Price — Regional Comparison",
            "Date",
            "Price (Gold)",
            dark_mode,
        )
    )
    return fig


def create_ohlc_chart(ohlc_df: pd.DataFrame, dark_mode: bool = False) -> go.Figure:
    """
    Candlestick chart built from daily OHLC aggregated data.

    Args:
        ohlc_df: DataFrame with columns date, open, high, low, close (as returned
                 by ``db_reader.build_ohlc_data``).
        dark_mode: Dark colour theme flag.
    """
    if ohlc_df.empty:
        return _empty_fig("Not enough data for OHLC view (need ≥ 7 days).", dark_mode)

    fig = go.Figure(
        go.Candlestick(
            x=ohlc_df["date"],
            open=ohlc_df["open"],
            high=ohlc_df["high"],
            low=ohlc_df["low"],
            close=ohlc_df["close"],
            name="Daily OHLC",
            increasing=dict(
                line=dict(color=COLOR_INCREASE, width=1),
                fillcolor=COLOR_INCREASE,
            ),
            decreasing=dict(
                line=dict(color=COLOR_DECREASE, width=1),
                fillcolor=COLOR_DECREASE,
            ),
            hovertext=[
                f"O: {row.open:,.0f}  H: {row.high:,.0f}  L: {row.low:,.0f}  C: {row.close:,.0f} Gold"
                for row in ohlc_df.itertuples()
            ],
        )
    )

    layout = _base_layout(
        "WoW Token Price — Daily OHLC",
        "Date",
        "Price (Gold)",
        dark_mode,
    )
    layout["xaxis"]["rangeslider"] = {"visible": False}
    fig.update_layout(**layout)
    return fig


def create_heatmap_figure(pivot_df: pd.DataFrame, dark_mode: bool = False) -> go.Figure:
    """
    Heatmap of the mean token price by UTC day-of-week (y-axis) and hour (x-axis).
    Green = cheaper, Red = more expensive.

    Args:
        pivot_df: Pivot DataFrame as returned by ``db_reader.build_heatmap_pivot``.
        dark_mode: Dark colour theme flag.
    """
    theme = _t(dark_mode)

    if pivot_df.empty:
        return _empty_fig(
            "Not enough data for heatmap (need full day/hour coverage).", dark_mode
        )

    hours = [f"{h:02d}:00" for h in pivot_df.columns.tolist()]
    days = pivot_df.index.tolist()
    z_values = pivot_df.values.tolist()

    fig = go.Figure(
        go.Heatmap(
            z=z_values,
            x=hours,
            y=days,
            colorscale=[
                [0.0, COLOR_INCREASE],
                [0.5, "#FFF176"],
                [1.0, COLOR_DECREASE],
            ],
            hovertemplate="<b>%{y}</b> at <b>%{x}</b><br>Avg: %{z:,.0f} Gold<extra></extra>",
            colorbar=dict(
                title=dict(text="Avg Gold", font=dict(color=theme["font"])),
                tickfont=dict(color=theme["font"]),
                tickformat=",d",
            ),
        )
    )

    fig.update_layout(
        title={
            "text": "Average Price by Day & Hour (UTC) — Green = cheaper",
            "x": 0.05,
            "font": {"size": 15},
        },
        xaxis_title="Hour (UTC)",
        yaxis_title="Day of Week",
        plot_bgcolor=theme["bg"],
        paper_bgcolor=theme["paper"],
        font={"color": theme["font"]},
        xaxis=dict(
            tickfont=dict(color=theme["font"]), title_font=dict(color=theme["font"])
        ),
        yaxis=dict(
            tickfont=dict(color=theme["font"]), title_font=dict(color=theme["font"])
        ),
        margin=dict(l=110, r=20, t=55, b=60),
    )
    return fig
