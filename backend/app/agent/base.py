"""
Abstract interface for all agents.
Enforces dependency injection of LLM and tools.
"""
from abc import ABC, abstractmethod

from app.agent.state import AgentState
from app.llm.base import LLMClient
from app.tools.registry import ToolRegistry


class Agent(ABC):
    """Base class for all agents."""

    def __init__(self, llm: LLMClient, tool_registry: ToolRegistry) -> None:
        self.llm = llm
        self.tool_registry = tool_registry

    @abstractmethod
    async def step(self, state: AgentState) -> AgentState:
        """
        Perform one iteration of the agent loop.
        Must be a pure function of state -> new state.
        """
        pass
