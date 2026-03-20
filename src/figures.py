import plotly.graph_objects as go
import pandas as pd
from config import EMA_SPAN_DAYS


def create_token_line_plot(df: pd.DataFrame) -> go.Figure:
    """
    Generates a Plotly line chart with the actual WoW token price and its EMA.
 
    Args:
        df: DataFrame containing 'datetime', 'price_gold', and 'ema' columns,
            pre-filtered to the desired time range.
 
    Returns:
        A configured Plotly Figure object.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["price_gold"],
            mode="lines",
            line=dict(color="#17B897", width=2, dash="solid"),
            name="Actual Price",
            hovertemplate=(
                "Date: %{x|%Y-%m-%d %H:%M:%S}<br>Price: %{y} Gold<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["ema"],
            mode="lines",
            line=dict(color="#FF6347", width=2, dash="dash"),
            name=f"EMA ({EMA_SPAN_DAYS}-day)",
            hovertemplate=(
                f"Date: %{{x|%Y-%m-%d %H:%M:%S}}<br>EMA: %{{y}} Gold"
                f"<extra>{EMA_SPAN_DAYS}-Day EMA</extra>"
            ),
        )
    )

    fig.update_layout(
        title={"text": "WoW Token Price Over Time", "x": 0.05, "xanchor": "left"},
        xaxis_title="Date",
        yaxis_title="Price (Gold)",
        xaxis_fixedrange=True,
        yaxis_fixedrange=True,
        hovermode="x unified",
        margin=dict(l=40, r=20, t=50, b=40),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font={"color": "#4b5563"},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig
