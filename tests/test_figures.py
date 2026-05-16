import pandas as pd
import plotly.graph_objects as go
from src.figures import create_token_line_plot


class TestCreateTokenLinePlot:
    def test_returns_figure_instance(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert isinstance(fig, go.Figure)
 
    def test_figure_has_four_traces(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert len(fig.data) == 4
 
    def test_third_trace_is_actual_price(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert fig.data[2].name == "Actual Price"
 
    def test_fourth_trace_is_ema(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert "EMA" in fig.data[3].name
 
    def test_traces_use_correct_columns(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert list(fig.data[2].y) == list(sample_df["price_gold"])
        assert list(fig.data[3].y) == list(sample_df["ema"])
 
    def test_empty_dataframe_returns_empty_figure_with_annotation(self):
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
        # _empty_fig returns a figure with no data traces and a text annotation
        assert len(fig.data) == 0
        assert len(fig.layout.annotations) > 0
        assert "Waiting" in fig.layout.annotations[0].text
 
    def test_layout_title_is_set(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert "WoW Token Price" in fig.layout.title.text
 
    def test_axes_are_fixed_range(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert fig.layout.xaxis.fixedrange is True
        assert fig.layout.yaxis.fixedrange is True
 
    def test_band_traces_have_no_legend_entry_and_skip_hover(self, sample_df):
        fig = create_token_line_plot(sample_df)
        upper = fig.data[0]
        assert upper.showlegend is False
        assert upper.hoverinfo == "skip"
 
    def test_ema_line_is_dashed(self, sample_df):
        fig = create_token_line_plot(sample_df)
        assert fig.data[3].line.dash == "dash"
