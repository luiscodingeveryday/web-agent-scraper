"""
Comprehensive unit tests for AgentRunner.
Tests happy paths, error handling, and edge cases.
"""
from unittest.mock import AsyncMock

import pytest
from app.agent.base import Agent
from app.agent.state import AgentState
from app.services.runner import AgentRunner

# ==================== HAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_runner_stops_immediately_with_final_answer():
    """Test: Agent returns final answer in first step."""
    agent = AsyncMock(spec=Agent)
    agent.step.return_value = AgentState(
        step_count=1,
        final_answer="The answer is 42"
    )

    runner = AgentRunner(agent, max_iterations=10)
    initial_state = AgentState()

    final_state = await runner.run(initial_state)

    # Should stop immediately
    assert final_state.final_answer == "The answer is 42"
    assert final_state.error is None
    assert agent.step.await_count == 1
    assert final_state.step_count == 1

@pytest.mark.asyncio
async def test_runner_completes_multi_step_workflow():
    """Test: Agent takes 3 steps before returning final answer."""
    agent = AsyncMock(spec=Agent)

    # Simulate 3 steps: 2 tool uses, then final answer
    agent.step.side_effect = [
        AgentState(step_count=1, scratchpad="Step 1: Used tool A"),
        AgentState(step_count=2, scratchpad="Step 2: Used tool B"),
        AgentState(step_count=3, scratchpad="Step 3: Done", final_answer="Result"),
    ]

    runner = AgentRunner(agent, max_iterations=10)
    initial_state = AgentState()

    final_state = await runner.run(initial_state)

    assert final_state.final_answer == "Result"
    assert final_state.error is None
    assert agent.step.await_count == 3
    assert final_state.step_count == 3


@pytest.mark.asyncio
async def test_runner_preserves_scratchpad():
    """Test: Runner preserves agent's scratchpad across steps."""
    agent = AsyncMock(spec=Agent)

    agent.step.side_effect = [
        AgentState(step_count=1, scratchpad="Observation 1"),
        AgentState(step_count=2, scratchpad="Observation 1\nObservation 2", final_answer="Done"),
    ]

    runner = AgentRunner(agent, max_iterations=10)
    initial_state = AgentState()

    final_state = await runner.run(initial_state)

    assert "Observation 1" in final_state.scratchpad
    assert "Observation 2" in final_state.scratchpad
    assert final_state.final_answer == "Done"

# ==================== UNHAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_runner_reaches_max_iterations_without_answer():
    """Test: Agent never returns final answer, hits max iterations."""
    agent = AsyncMock(spec=Agent)

    # Agent keeps returning incomplete states
    agent.step.side_effect = [
        AgentState(step_count=1),
        AgentState(step_count=2),
        AgentState(step_count=3),
    ]

    runner = AgentRunner(agent, max_iterations=3)
    initial_state = AgentState()

    final_state = await runner.run(initial_state)

    # Should have error set by runner
    assert final_state.error == "Max iterations (3) reached without final answer."
    assert final_state.final_answer is None
    assert agent.step.await_count == 3


@pytest.mark.asyncio
async def test_runner_handles_agent_exception():
    """Test: Agent.step() raises an exception."""
    agent = AsyncMock(spec=Agent)
    agent.step.side_effect = RuntimeError("Agent crashed unexpectedly")

    runner = AgentRunner(agent, max_iterations=10)
    initial_state = AgentState()

    # Should propagate exception (runner doesn't catch)
    with pytest.raises(RuntimeError, match="Agent crashed unexpectedly"):
        await runner.run(initial_state)
