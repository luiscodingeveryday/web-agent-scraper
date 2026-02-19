"""
Registry for all available tools.
Allows injection of tools and lookup by name.
"""
from typing import Dict, Optional

from app.tools.base import Tool


class ToolRegistry:
    """Container for tools, injectable into agent."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Add a tool to the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list_all(self) -> Dict[str, Tool]:
        """Return all registered tools."""
        return self._tools.copy()
