import plotly.graph_objects as go
import pandas as pd

def create_token_line_plot(df: pd.DataFrame):
    """
    Generates the Plotly line chart for token prices.

    Args:
        df: A Pandas DataFrame expected to contain 'datetime', 'price_gold', 
            and 'ema' columns.
    
    Returns:
        A Plotly Figure object configured with the line traces and layout.
    """
    # Initialize a new Plotly Figure object.
    line_figure = go.Figure()

    # Add the trace for the actual token price
    line_figure.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["price_gold"],
            mode="lines+markers",
            line=dict(color="#17B897", width=2, dash="solid"),
            name="Actual Price",
            hovertemplate=(
                "Date: %{x|%Y-%m-%d %H:%M:%S}<br>"
                "Price: %{y} Gold<extra></extra>"
            ),
        )
    )

    # Add the trace for the Exponential Moving Average (EMA)
    line_figure.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["ema"],
            mode="lines",
            line=dict(color="#FF6347", width=2, dash="dash"),
            name="Exponential Moving Average (7 days)",
            hovertemplate=(
                "Date: %{x|%Y-%m-%d %H:%M:%S}<br>"
                "EMA: %{y} Gold<extra>7-Day EMA</extra>"
            ),
        )
    )

    # Update the chart layout and aesthetics
    line_figure.update_layout(
        title={
            "text": "WoW Token Price Over Time",
            "x": 0.05,
            "xanchor": "left"
        },
        xaxis_title="Date",
        yaxis_title="Price (Gold)",
        xaxis_fixedrange=True,
        yaxis_fixedrange=True,
        legend_title="Legend",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return line_figure