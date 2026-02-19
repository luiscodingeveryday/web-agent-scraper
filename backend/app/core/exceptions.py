"""
Custom exception hierarchy for clean error handling.
"""


class AgentError(Exception):
    """Base exception for agent-related errors."""

    pass


class LLMError(AgentError):
    """Raised when the LLM call fails or returns invalid format."""

    pass


class ToolExecutionError(AgentError):
    """Raised when a tool fails during execution."""

    pass


class AgentMaxIterationsError(AgentError):
    """Raised when the agent exceeds the maximum step limit."""

    pass


class ConfigurationError(Exception):
    """Raised for invalid configuration."""

    pass
