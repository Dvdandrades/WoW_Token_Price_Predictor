import pandas as pd
from dash import html

from src.callbacks import _filter_by_days, _price_change_spans


# _filter_by_days
class TestFilterByDays:
    def test_returns_full_df_when_days_filter_is_zero(self, sample_df):
        result = _filter_by_days(sample_df, 0)
        assert len(result) == len(sample_df)

    def test_returns_full_df_when_empty(self):
        empty = pd.DataFrame(columns=["datetime", "price_gold"])
        result = _filter_by_days(empty, 3)
        assert result.empty

    def test_filters_to_last_n_days(self, sample_df):
        # sample_df spans 5 intervals of 20 min — well within 1 day
        result = _filter_by_days(sample_df, 1)
        assert not result.empty
        assert len(result) == len(sample_df)

    def test_excludes_old_rows(self):
        df = pd.DataFrame(
            {
                "datetime": pd.to_datetime(["2024-01-01", "2024-01-10"]),
                "price_gold": [100_000, 200_000],
            }
        )
        result = _filter_by_days(df, 3)
        assert len(result) == 1
        assert result.iloc[0]["price_gold"] == 200_000

    def test_converts_string_datetime_column(self):
        df = pd.DataFrame(
            {
                "datetime": ["2024-01-09 00:00:00", "2024-01-10 00:00:00"],
                "price_gold": [100_000, 200_000],
            }
        )
        result = _filter_by_days(df, 3)
        assert len(result) == 2


# _format_price_change_indicators
class TestPriceChangeSpans:
    def test_returns_na_span_for_nan_change(self):
        result = _price_change_spans(float("nan"), 0.0)
        assert isinstance(result, html.Span)
        assert "N/A" in result.children

    def test_returns_na_span_for_none_change(self):
        result = _price_change_spans(None, 0.0)
        assert isinstance(result, html.Span)

    def test_positive_change_uses_increase_color(self):
        spans = _price_change_spans(1_000, 0.5)
        assert isinstance(spans, list)
        assert "#17B897" in spans[0].style["color"]

    def test_negative_change_uses_decrease_color(self):
        spans = _price_change_spans(-1_000, -0.5)
        assert "#FF6347" in spans[0].style["color"]

    def test_zero_change_treated_as_positive(self):
        spans = _price_change_spans(0, 0.0)
        assert "#17B897" in spans[0].style["color"]

    def test_positive_change_has_plus_sign(self):
        spans = _price_change_spans(500, 0.2)
        assert "+" in spans[0].children

    def test_negative_change_has_no_plus_sign(self):
        spans = _price_change_spans(-500, -0.2)
        assert "+" not in spans[0].children

    def test_pct_formatted_to_two_decimals(self):
        spans = _price_change_spans(1_000, 0.333333)
        pct_text = spans[1].children
        assert "0.33" in pct_text
