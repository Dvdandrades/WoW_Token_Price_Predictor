import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api_client import BlizzardAPIClient


# Helpers
def _make_client(tmp_path: Path) -> BlizzardAPIClient:
    return BlizzardAPIClient(
        client_id="test_id",
        client_secret="test_secret",
        region="eu",
        locale="en_US",
        token_cache_file=tmp_path / "token_cache.json",
    )


# Initialisation
def test_raises_on_missing_credentials(tmp_path):
    with pytest.raises(ValueError, match="CLIENT_ID"):
        BlizzardAPIClient("", "", "eu", "en_US", tmp_path / "cache.json")


def test_region_specific_cache_filename(tmp_path):
    client = _make_client(tmp_path)
    assert client.token_cache_file.name == "token_cache_eu.json"


# Token cache
def test_load_token_cache_return_none_when_file_missing(tmp_path):
    client = _make_client(tmp_path)
    assert client._load_token_cache() is None


def test_load_token_cache_returns_none_for_expired_token(tmp_path):
    client = _make_client(tmp_path)
    data = {"access_token": "old_token", "expiry": time.time() - 10}
    client.token_cache_file.write_text(json.dumps(data))

    assert client._load_token_cache() is None
    assert not client.token_cache_file.exists()  # stale file removed


def test_load_token_cache_returns_token_when_valid(tmp_path):
    client = _make_client(tmp_path)
    data = {"access_token": "valid_token", "expiry": time.time() + 3600}
    client.token_cache_file.write_text(json.dumps(data))

    assert client._load_token_cache() == "valid_token"


def test_save_token_cache_writes_file(tmp_path):
    client = _make_client(tmp_path)
    client._save_token_cache("new_token", 3600)

    data = json.loads(client.token_cache_file.read_text())
    assert client.token_cache_file.exists()
    assert data["access_token"] == "new_token"
    assert data["expiry"] > time.time()


# get_access_token
def test_get_access_token_uses_cache(tmp_path):
    client = _make_client(tmp_path)
    data = {"access_token": "cached", "expiry": time.time() + 3600}
    client.token_cache_file.write_text(json.dumps(data))

    with patch.object(client.session, "post") as mock_post:
        token = client.get_access_token()

    assert token == "cached"
    mock_post.assert_not_called()


def test_get_access_token_requests_new_when_cache_empty(tmp_path):
    client = _make_client(tmp_path)

    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "fresh", "expires_in": 3600}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client.session, "post", return_value=mock_response):
        token = client.get_access_token()

    assert token == "fresh"
    assert client.token_cache_file.exists()


def test_get_access_token_raises_on_http_error(tmp_path):
    client = _make_client(tmp_path)

    with patch.object(
        client.session, "post", side_effect=requests.exceptions.ConnectionError("err")
    ):
        with pytest.raises(requests.exceptions.RequestException):
            client.get_access_token()


# fetch_wow_token_price
def test_fetch_wow_token_price_returns_int(tmp_path):
    client = _make_client(tmp_path)
    client._access_token = "token"

    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "token", "expires_in": 3600}
    mock_token_resp.raise_for_status = MagicMock()

    mock_price_resp = MagicMock()
    mock_price_resp.json.return_value = {"price": 3_000_000_000}
    mock_price_resp.raise_for_status = MagicMock()

    with (
        patch.object(client.session, "post", return_value=mock_token_resp),
        patch.object(client.session, "get", return_value=mock_price_resp),
    ):
        price = client.fetch_wow_token_price()

    assert price == 3_000_000_000


def test_fetch_wow_token_price_raises_on_missing_price_key(tmp_path):
    client = _make_client(tmp_path)

    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "token", "expires_in": 3600}
    mock_token_resp.raise_for_status = MagicMock()

    mock_price_resp = MagicMock()
    mock_price_resp.json.return_value = {"unexpected": "data"}
    mock_price_resp.raise_for_status = MagicMock()

    with (
        patch.object(client.session, "post", return_value=mock_token_resp),
        patch.object(client.session, "get", return_value=mock_price_resp),
    ):
        with pytest.raises(KeyError, match="price"):
            client.fetch_wow_token_price()
