"""
Comprehensive unit tests for ScraperTool.
"""
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from app.tools.implementations.scraper import ScraperTool, StaticScraper

# ==================== FIXTURES ====================

@pytest.fixture
def create_http_response():
    """Factory for creating mock HTTP responses."""
    def _create(content: str, status_code: int = 200, content_type: str = "text/html"):
        response = MagicMock(spec=httpx.Response)
        response.text = content
        response.content = content.encode()
        response.status_code = status_code

        headers = MagicMock()
        headers.get = MagicMock(return_value=content_type)
        response.headers = headers

        if status_code >= 400:
            response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    f"HTTP {status_code}",
                    request=MagicMock(),
                    response=response
                )
            )
        else:
            response.raise_for_status = MagicMock()

        return response
    return _create


# ==================== HAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_scraper_extracts_text_from_simple_html(mock_http_client, create_http_response):
    """Test: Extracts visible text from basic HTML."""
    html = "<html><body><h1>Title</h1><p>Hello World</p></body></html>"
    mock_http_client.get = AsyncMock(return_value=create_http_response(html))

    scraper = StaticScraper(mock_http_client)
    result = await scraper.scrape("https://example.com")

    assert "Title" in result
    assert "Hello World" in result


@pytest.mark.asyncio
async def test_scraper_removes_script_tags(mock_http_client, create_http_response):
    """Test: Script tag content is removed from output."""
    html = "<html><body><script>alert('evil')</script><p>Clean text</p></body></html>"
    mock_http_client.get = AsyncMock(return_value=create_http_response(html))

    scraper = StaticScraper(mock_http_client)
    result = await scraper.scrape("https://example.com")

    assert "alert" not in result
    assert "evil" not in result
    assert "Clean text" in result


@pytest.mark.asyncio
async def test_scraper_removes_style_tags(mock_http_client, create_http_response):
    """Test: Style tag content is removed from output."""
    html = """<html>
        <head><style>body{color:red;}</style></head>
        <body><p>Visible</p></body>
    </html>"""
    mock_http_client.get = AsyncMock(return_value=create_http_response(html))

    scraper = StaticScraper(mock_http_client)
    result = await scraper.scrape("https://example.com")

    assert "color:red" not in result
    assert "Visible" in result


@pytest.mark.asyncio
async def test_scraper_truncates_long_content(mock_http_client, create_http_response):
    """Test: Very long content is truncated."""
    long_text = "Lorem ipsum " * 2000
    html = f"<html><body><p>{long_text}</p></body></html>"
    mock_http_client.get = AsyncMock(return_value=create_http_response(html))

    scraper = StaticScraper(mock_http_client)
    result = await scraper.scrape("https://example.com")

    assert "truncated" in result.lower()
    assert len(result) < len(long_text)


# ==================== UNHAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_scraper_handles_network_error(mock_http_client):
    """Test: Network errors return error message."""
    mock_http_client.get = AsyncMock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    scraper = StaticScraper(mock_http_client)
    result = await scraper.scrape("https://unreachable.com")

    assert "Failed to fetch" in result or "Connection refused" in result


@pytest.mark.asyncio
async def test_scraper_handles_timeout(mock_http_client):
    """Test: Timeout errors return error message."""
    mock_http_client.get = AsyncMock(
        side_effect=httpx.TimeoutException("Request timeout")
    )

    scraper = StaticScraper(mock_http_client)
    result = await scraper.scrape("https://slow.com")

    assert "Failed to fetch" in result or "timeout" in result.lower()


@pytest.mark.asyncio
async def test_scraper_detects_non_html_content(mock_http_client, create_http_response):
    """Test: Non-HTML content type is detected."""
    response = create_http_response("Binary data", content_type="application/pdf")
    mock_http_client.get = AsyncMock(return_value=response)

    scraper = StaticScraper(mock_http_client)
    result = await scraper.scrape("https://example.com/file.pdf")

    assert "application/pdf" in result
    assert "Only HTML pages" in result


@pytest.mark.asyncio
async def test_scraper_handles_empty_html(mock_http_client, create_http_response):
    """Test: Empty HTML body returns minimal text."""
    html = "<html><body></body></html>"
    mock_http_client.get = AsyncMock(return_value=create_http_response(html))

    scraper = StaticScraper(mock_http_client)
    result = await scraper.scrape("https://example.com")

    assert isinstance(result, str)


# ==================== CONTRACT TESTS ====================

def test_scraper_has_correct_name():
    """Test: Tool name is 'scraper'."""
    scraper = ScraperTool(None)
    assert scraper.name == "scraper"


def test_scraper_has_description():
    """Test: Tool has non-empty description."""
    scraper = ScraperTool(None)
    assert scraper.description != ""
    assert len(scraper.description) > 20
