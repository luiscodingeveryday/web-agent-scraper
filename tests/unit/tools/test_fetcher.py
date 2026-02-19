"""
Comprehensive unit tests for FetcherTool.
Tests happy paths, error handling, and edge cases.
"""
from unittest.mock import MagicMock

import httpx
import pytest
from app.tools.implementations.fetcher import FetcherTool

# ==================== HAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_fetcher_returns_html_content(mock_http_client):
    """Test: Fetcher returns HTML content from URL."""
    mock_http_client.get.return_value.content = b"<html><body>Hello World</body></html>"
    fetcher = FetcherTool(mock_http_client)
    result = await fetcher.execute("https://example.com")
    assert "Hello World" in result
    assert result != ""


@pytest.mark.asyncio
async def test_fetcher_adds_https_to_url_without_scheme(mock_http_client):
    """Test: URL without http:// gets https:// prepended."""
    fetcher = FetcherTool(mock_http_client)
    await fetcher.execute("example.com")
    call_args = mock_http_client.get.call_args
    called_url = call_args[0][0]
    assert called_url.startswith("https://")


@pytest.mark.asyncio
async def test_fetcher_preserves_https_url(mock_http_client):
    """Test: URL with https:// is not modified."""
    fetcher = FetcherTool(mock_http_client)
    await fetcher.execute("https://example.com/page")
    call_args = mock_http_client.get.call_args
    called_url = call_args[0][0]
    assert called_url == "https://example.com/page"


# ==================== UNHAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_fetcher_returns_error_message_on_404(mock_http_client):
    """Test: 404 response returns error string, does NOT raise exception."""
    error_response = MagicMock()
    error_response.status_code = 404
    error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found",
        request=MagicMock(),
        response=error_response
    )
    mock_http_client.get.return_value = error_response

    fetcher = FetcherTool(mock_http_client)
    result = await fetcher.execute("https://example.com/notfound")
    assert "Error HTTP 404" in result or "HTTP Error 404" in result


@pytest.mark.asyncio
async def test_fetcher_retries_on_403_then_returns_error(mock_http_client):
    """Test: 403 triggers retry (2 attempts), then returns error string."""
    error_response = MagicMock()
    error_response.status_code = 403
    error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Forbidden",
        request=MagicMock(),
        response=error_response
    )
    mock_http_client.get.return_value = error_response

    fetcher = FetcherTool(mock_http_client)
    result = await fetcher.execute("https://example.com")
    assert "403" in result or "Error" in result
    assert mock_http_client.get.await_count == 2


@pytest.mark.asyncio
async def test_fetcher_returns_error_on_network_failure(mock_http_client):
    """Test: Network error returns error string, does NOT raise."""
    mock_http_client.get.side_effect = httpx.ConnectError("Connection refused")
    fetcher = FetcherTool(mock_http_client)
    result = await fetcher.execute("https://unreachable.com")
    assert "Error fetching" in result or "Error" in result
    assert "unreachable.com" in result


# ==================== TOOL CONTRACT TESTS ====================

def test_fetcher_has_correct_name():
    """Test: Tool name is 'fetcher'."""
    fetcher = FetcherTool(None)
    assert fetcher.name == "fetcher"
