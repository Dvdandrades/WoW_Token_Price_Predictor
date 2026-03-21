import pandas as pd
import plotly.graph_objects as go
from src.figures import create_token_line_plot


class TestCreateTokenLinePlot:
    def test_returns_figure_instance(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert isinstance(fig, go.Figure)

    def test_figure_has_two_traces(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert len(fig.data) == 2

    def test_first_trace_is_actual_price(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert fig.data[0].name == "Actual Price"

    def test_second_trace_is_ema(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert "EMA" in fig.data[1].name

    def test_traces_use_correct_columns(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert list(fig.data[0].y) == list(sample_df["price_gold"])
        assert list(fig.data[1].y) == list(sample_df["ema"])

    def test_empty_dataframe_produces_empty_traces(self):
        empty = pd.DataFrame(
            columns=[
                "datetime",
                "price_gold",
                "ema",
                "price_change_abs",
                "price_change_pct",
            ]
        )
        fig = create_token_line_plot(empty)
        assert len(fig.data) == 2
        assert fig.data[0].y is None or len(fig.data[0].y) == 0

    def test_layout_title_is_set(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert "WoW Token Price" in fig.layout.title.text

    def test_axes_are_fixed_range(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert fig.layout.xaxis.fixedrange is True
        assert fig.layout.yaxis.fixedrange is True
