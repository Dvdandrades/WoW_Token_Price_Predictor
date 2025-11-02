import plotly.express as px
import pandas as pd

def create_token_line_plot(df: pd.DataFrame):
    """Generates the Plotly line chart for token prices."""
    line_figure = px.line(
        df,
        x="datetime",
        y="price_gold",
        title="WoW Token Price Over Time",
    )

    # Update traces for styling (line color, markers) and custom hover text formatting.
    line_figure.update_traces(
        mode="lines+markers",
        line_color="#17B897",
        hovertemplate=(
            "Date: %{x|%Y-%m-%d %H:%M:%S}<br>"
            "Price: %{y} Gold<extra></extra>"
        ),
    )

    # Update layout for aesthetics: title position, axis labels, and fixed ranges.
    line_figure.update_layout(
        title_x=0.05,
        title_xanchor="left",
        xaxis_title="Date",
        yaxis_title="Price (Gold)",
        xaxis_fixedrange=True,
        yaxis_fixedrange=True,
    )

    return line_figure