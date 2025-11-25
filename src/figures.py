import plotly.graph_objects as go
import pandas as pd


def create_token_line_plot(df: pd.DataFrame) -> go.Figure:
    """
    Generates a Plotly line chart displaying the actual WoW token price and
    its Exponential Moving Average over time.

    Args:
        df: A Pandas DataFrame expected to contain 'datetime', 'price_gold',
            and 'ema' columns. The DataFrame must already be filtered by the
            desired time range.

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
            mode="lines",
            line=dict(color="#17B897", width=2, dash="solid"),
            name="Actual Price",
            # Custom hover text format
            hovertemplate=(
                "Date: %{x|%Y-%m-%d %H:%M:%S}<br>Price: %{y} Gold<extra></extra>"
            ),
        )
    )

    # Add the trace for the Exponential Moving Average
    line_figure.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["ema"],
            mode="lines",
            line=dict(color="#FF6347", width=2, dash="dash"),
            name="Exponential Moving Average (7 days)",
            # Custom hover text format
            hovertemplate=(
                "Date: %{x|%Y-%m-%d %H:%M:%S}<br>EMA: %{y} Gold<extra>7-Day EMA</extra>"
            ),
        )
    )

    # Update the chart layout and aesthetics
    line_figure.update_layout(
        title={"text": "WoW Token Price Over Time", "x": 0.05, "xanchor": "left"},
        xaxis_title="Date",
        yaxis_title="Price (Gold)",
        # Prevent zooming to keep the display clean
        xaxis_fixedrange=True,
        yaxis_fixedrange=True,
        # Display all traces' data when hovering over a single point on the x-axis
        hovermode="x unified",
        margin=dict(l=40, r=20, t=50, b=40),
        # Set background to white for a clean look
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font={"color": "#4b5563"},
        # Horizontal legend at the top right
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return line_figure
