"""
Orchestrates the agent loop.
Receives agent via DI, calls step until termination or max iterations.
"""
from app.agent.base import Agent
from app.agent.state import AgentState


class AgentRunner:
    """Application service that runs the agent loop."""

    def __init__(self, agent: Agent, max_iterations: int = 10):
        self._agent = agent
        self._max_iterations = max_iterations

    async def run(self, initial_state: AgentState) -> AgentState:
        """
        Execute the agent loop until final answer, error, or max iterations.
        Returns the final state.
        """
        state = initial_state

        if hasattr(self._agent, "_metrics"):
            from app.agent.react import ExecutionMetrics

            self._agent._metrics = ExecutionMetrics()

        while not state.final_answer and not state.error and state.step_count < self._max_iterations:
            state = await self._agent.step(state)

        if not state.final_answer and not state.error:
            state = state.model_copy(error=f"Max iterations ({self._max_iterations}) reached without final answer.")
        return state
