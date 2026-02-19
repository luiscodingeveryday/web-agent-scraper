"""
Abstract base class for all tools.
Each tool has a name, description, and an async execute method.
"""
from abc import ABC, abstractmethod


class Tool(ABC):
    """Interface that all tools must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does (for LLM)."""
        pass

    @abstractmethod
    async def execute(self, input_data: str) -> str:
        """
        Execute the tool with given input and return result as string.
        Must be stateless and idempotent.
        """
        pass
