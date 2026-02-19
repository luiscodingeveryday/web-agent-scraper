"""
Immutable agent state using Pydantic.
Each step produces a new state instance.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Represents the complete state of the agent at any point."""

    messages: List[dict] = Field(default_factory=list)  # Chat history
    scratchpad: str = ""  # Reasoning scratchpad
    step_count: int = 0
    final_answer: Optional[str] = None
    error: Optional[str] = None

    def model_copy(self, **kwargs) -> "AgentState":
        """Immutable update – produce a new instance with changes."""
        if "update" in kwargs:
            # Called as model_copy(update={...}) - pass through directly
            return super().model_copy(update=kwargs["update"], deep=True)
        elif kwargs:
            # Called as model_copy(field=value, ...) - wrap in update dict
            return super().model_copy(update=kwargs, deep=True)
        return super().model_copy(deep=True)
