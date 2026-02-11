import pytest
from unittest.mock import MagicMock, patch
from src.data_manager import save_price

@patch("src.data_manager.get_db_connection")
def test_ema_calculation_logic(mock_get_conn):

    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_get_conn.return_value.__enter__.return_value = mock_conn

    mock_cursor.fetchone.return_value = (100000, 100000.0)

    save_price(110000 * 10000, "eu")

    args, _ = mock_cursor.execute.call_args_list[-1]
    inserted_values = args[1]

    assert inserted_values[3] == 102500
    assert inserted_values[4] == 10000