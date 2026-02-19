from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from app.llm.base import LLMClient
from app.tools.base import Tool
from app.tools.registry import ToolRegistry


@pytest.fixture
def mock_llm() -> LLMClient:
    """Fixture for a mocked LLM client."""
    mock = AsyncMock(spec=LLMClient)
    mock.generate.return_value = '{"thought": "test", "action": "Final Answer", "action_input": "42"}'
    return mock

@pytest.fixture
def mock_tool_registry() -> ToolRegistry:
    """Fixture for a tool registry with no tools."""
    return ToolRegistry()

@pytest.fixture
def mock_http_client():
    """Fixture for a mocked HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    # Configurar respuesta por defecto
    response = AsyncMock()
    response.content = b"<html><body>Mocked response</body></html>"
    response.status_code = 200
    response.raise_for_status = AsyncMock()
    # Headers necesarios para scraper
    headers = MagicMock()
    headers.get.return_value = 'text/html; charset=utf-8'
    response.headers = headers
    client.get.return_value = response
    return client

@pytest.fixture
def mock_tool():
    """Mock tool that returns a fixed result."""
    tool = AsyncMock(spec=Tool)
    tool.name = "test_tool"
    tool.description = "A test tool"
    tool.execute = AsyncMock(return_value="Tool result")
    return tool
