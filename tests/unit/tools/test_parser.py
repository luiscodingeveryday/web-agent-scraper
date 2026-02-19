"""
Comprehensive unit tests for ParserTool.
"""
import pytest
from app.tools.implementations.parser import ParserTool


@pytest.fixture
def parser():
    return ParserTool()


# ==================== HAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_parser_extracts_single_email(parser):
    """Test: Extracts one email from text."""
    result = await parser.execute("emails\nContact us at hello@example.com")
    assert "hello@example.com" in result


@pytest.mark.asyncio
async def test_parser_extracts_multiple_emails(parser):
    """Test: Extracts multiple emails from text."""
    result = await parser.execute("emails\nContact test@example.com and admin@site.org")
    assert "test@example.com" in result
    assert "admin@site.org" in result


@pytest.mark.asyncio
async def test_parser_extracts_single_url(parser):
    """Test: Extracts one URL from text."""
    result = await parser.execute("urls\nVisit https://example.com for more info")
    assert "https://example.com" in result


@pytest.mark.asyncio
async def test_parser_extracts_multiple_urls(parser):
    """Test: Extracts multiple URLs from text."""
    result = await parser.execute("urls\nVisit https://example.com and http://test.org")
    assert "https://example.com" in result
    assert "http://test.org" in result

# ==================== UNHAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_parser_returns_message_when_no_emails_found(parser):
    """Test: Returns 'No emails found.' when text has no emails."""
    result = await parser.execute("emails\nThis text has no email addresses")
    assert result == "No emails found."


@pytest.mark.asyncio
async def test_parser_returns_message_when_no_urls_found(parser):
    """Test: Returns 'No URLs found.' when text has no URLs."""
    result = await parser.execute("urls\nThis text has no URLs")
    assert result == "No URLs found."


@pytest.mark.asyncio
async def test_parser_returns_error_on_unknown_command(parser):
    """Test: Unknown command returns error message."""
    result = await parser.execute("phones\nCall 123-456-7890")
    assert "Unknown parser command" in result
    assert "phones" in result

# ==================== CONTRACT TESTS ====================

def test_parser_has_correct_name(parser):
    """Test: Tool name is 'parser'."""
    assert parser.name == "parser"


def test_parser_has_description(parser):
    """Test: Tool has non-empty description."""
    assert parser.description != ""
    assert len(parser.description) > 10
