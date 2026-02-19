"""
Comprehensive unit tests for ReActAgent.
Tests happy paths, error handling, and edge cases.
"""
import pytest
from app.agent.react import ReActAgent
from app.agent.state import AgentState
from app.core.exceptions import ToolExecutionError

# ==================== HAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_agent_returns_final_answer_directly(mock_llm, mock_tool_registry):
    """Test: LLM returns Final Answer immediately."""
    mock_llm.generate.return_value = '{"thought": "I know the answer", "action": "Final Answer", "action_input": "42"}'

    agent = ReActAgent(mock_llm, mock_tool_registry)
    state = AgentState(messages=[{"role": "user", "content": "What is the answer?"}])

    new_state = await agent.step(state)

    assert new_state.final_answer == "42"
    assert new_state.step_count == 1
    assert new_state.error is None
    assert "Final Answer" in new_state.scratchpad


@pytest.mark.asyncio
async def test_agent_uses_tool_then_continues(mock_llm, mock_tool_registry, mock_tool):
    """Test: Agent uses a tool and continues (no final answer yet)."""
    mock_tool_registry.register(mock_tool)
    agent = ReActAgent(mock_llm, mock_tool_registry)

    mock_llm.generate.return_value = '{"thought": "I need to use the tool", "action": "test_tool", "action_input": "some input"}'

    state = AgentState(messages=[{"role": "user", "content": "Use the tool"}])
    new_state = await agent.step(state)

    # Should NOT have final answer yet
    assert new_state.final_answer is None
    assert new_state.error is None
    assert new_state.step_count == 1

    # Should have executed the tool
    mock_tool.execute.assert_awaited_once_with("some input")
    # Usar marcador '📊 Result:' en lugar de 'Observation:'
    assert "📊 Result: Tool result" in new_state.scratchpad


@pytest.mark.asyncio
async def test_agent_multi_step_workflow(mock_llm, mock_tool_registry, mock_tool):
    """Test: Agent performs multiple steps before final answer."""
    mock_tool_registry.register(mock_tool)
    agent = ReActAgent(mock_llm, mock_tool_registry)

    # Step 1: Use tool
    mock_llm.generate.return_value = '{"thought": "Use tool first", "action": "test_tool", "action_input": "query"}'
    state = AgentState(messages=[{"role": "user", "content": "Multi-step task"}])
    state = await agent.step(state)

    assert state.step_count == 1
    assert state.final_answer is None

    # Step 2: Give final answer
    mock_llm.generate.return_value = '{"thought": "Now I have enough info", "action": "Final Answer", "action_input": "Complete"}'
    state = await agent.step(state)

    assert state.step_count == 2
    assert state.final_answer == "Complete"


@pytest.mark.asyncio
async def test_agent_with_long_result_truncates(mock_llm, mock_tool_registry, mock_tool):
    """Test: Long tool results are truncated (threshold 10000 chars)."""
    mock_tool_registry.register(mock_tool)
    agent = ReActAgent(mock_llm, mock_tool_registry)

    # Create a result of 2000 characters (less than 10000, must not be truncated)
    long_result = "x" * 2000
    mock_tool.execute.return_value = long_result
    mock_llm.generate.return_value = '{"thought": "Get data", "action": "test_tool", "action_input": "input"}'

    state = AgentState()
    new_state = await agent.step(state)

    # Verify that the scratchpad contains the full result
    assert len(new_state.scratchpad) > 2000
    assert "(truncated)" not in new_state.scratchpad


# ==================== UNHAPPY PATH TESTS ====================

@pytest.mark.asyncio
async def test_agent_handles_llm_error(mock_llm, mock_tool_registry):
    """Test: LLM throws exception."""
    mock_llm.generate.side_effect = Exception("API timeout")

    agent = ReActAgent(mock_llm, mock_tool_registry)
    state = AgentState()
    new_state = await agent.step(state)

    assert new_state.error is not None
    assert "LLM service unavailable" in new_state.error
    assert "API timeout" in new_state.error
    assert new_state.step_count == 1


@pytest.mark.asyncio
async def test_agent_handles_invalid_json(mock_llm, mock_tool_registry):
    """Test: LLM returns invalid JSON."""
    mock_llm.generate.return_value = "This is not JSON at all!"

    agent = ReActAgent(mock_llm, mock_tool_registry)
    state = AgentState()
    new_state = await agent.step(state)

    # Should fallback to treating response as Final Answer
    assert new_state.final_answer == "This is not JSON at all!"
    assert new_state.error is None


@pytest.mark.asyncio
async def test_agent_handles_tool_execution_error(mock_llm, mock_tool_registry, mock_tool):
    """Test: Tool raises ToolExecutionError during execution."""
    mock_tool_registry.register(mock_tool)
    agent = ReActAgent(mock_llm, mock_tool_registry)

    mock_tool.execute.side_effect = ToolExecutionError("Network error")
    mock_llm.generate.return_value = '{"thought": "Use tool", "action": "test_tool", "action_input": "data"}'

    state = AgentState()
    new_state = await agent.step(state)

    # Should NOT have error flag (continues with observation)
    assert new_state.error is None
    assert "Tool execution error" in new_state.scratchpad
    assert "Network error" in new_state.scratchpad
    assert new_state.step_count == 1
