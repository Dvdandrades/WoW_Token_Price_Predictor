import pytest
import pandas as pd
from dash import html
from src.callbacks import _format_price_change_indicators, _filter_dataframe_by_days

def test_format_price_change_indicators_positive():
    abs_change = 5000
    pct_change = 2.5

    result = _format_price_change_indicators(abs_change, pct_change)

    assert "+" in result[1].children
    assert "2.50%" in result[1].children
    assert result[1].style["color"] == "#17B897"

def test_format_price_change_indicators_negative():
    abs_change = -3000
    pct_change = -1.5

    result = _format_price_change_indicators(abs_change, pct_change)

    assert "-" in result[1].children
    assert "-1.50%" in result[1].children
    assert result[1].style["color"] == "#FF6347"