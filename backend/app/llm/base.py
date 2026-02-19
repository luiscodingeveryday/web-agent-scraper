"""
Abstract interface for LLM clients.
Enables swapping Ollama with any other provider.
"""
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Interface for all LLM adapters."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Send prompt to LLM and return the generated text."""
        pass
