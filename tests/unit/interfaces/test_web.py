"""
Comprehensive unit tests for FastAPI endpoints.
Tests happy paths, error handling, and edge cases.
"""
from unittest.mock import AsyncMock

import pytest
from app.agent.state import AgentState
from app.interfaces.web import create_app
from app.services.runner import AgentRunner
from fastapi.testclient import TestClient

# ==================== FIXTURES ====================

@pytest.fixture
def mock_runner():
    """Mock runner that returns a successful state."""
    runner = AsyncMock(spec=AgentRunner)
    runner.run.return_value = AgentState(
        final_answer="The answer is 42",
        scratchpad="User: What is the answer?\nThought: I know it",
        step_count=1
    )
    return runner


@pytest.fixture
def client(mock_runner):
    """Test client with mocked runner."""
    app = create_app(mock_runner)
    return TestClient(app)


# ==================== HAPPY PATH TESTS ====================

def test_health_endpoint(client):
    """Test: /api/health endpoint returns 200 OK."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_agent_run_with_valid_input(client, mock_runner):
    """Test: POST /agent/run with valid user_input returns success."""
    response = client.post(
        "/api/agent/run",
        json={"user_input": "What is the capital of France?"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["final_answer"] == "The answer is 42"
    assert data["scratchpad"] == "User: What is the answer?\nThought: I know it"
    assert data["error"] is None
    assert data["steps"] == 1

    # Verify runner was called
    mock_runner.run.assert_awaited_once()


def test_agent_run_creates_initial_state_correctly(client, mock_runner):
    """Test: Endpoint creates initial state with correct format."""
    client.post(
        "/api/agent/run",
        json={"user_input": "Test query"}
    )

    # Get the state passed to runner
    call_args = mock_runner.run.call_args
    initial_state = call_args[0][0]

    # Verify initial state structure
    assert initial_state.messages == [{"role": "user", "content": "Test query"}]
    assert "Test query" in initial_state.scratchpad
    assert initial_state.step_count == 0
    assert initial_state.final_answer is None
    assert initial_state.error is None


def test_agent_run_with_long_input(client, mock_runner):
    """Test: Endpoint handles long user input."""
    long_input = "x" * 10000  # 10K characters

    response = client.post(
        "/api/agent/run",
        json={"user_input": long_input}
    )

    assert response.status_code == 200
    mock_runner.run.assert_awaited_once()


def test_agent_run_with_special_characters(client, mock_runner):
    """Test: Endpoint handles special characters in input."""
    special_input = "Test with émojis 😀 and symbols: @#$%^&*()"

    response = client.post(
        "/api/agent/run",
        json={"user_input": special_input}
    )

    assert response.status_code == 200

    # Verify special chars were preserved
    call_args = mock_runner.run.call_args
    initial_state = call_args[0][0]
    assert special_input in initial_state.scratchpad


def test_agent_run_returns_error_from_runner(client, mock_runner):
    """Test: Endpoint correctly returns error from runner."""
    # Mock runner returns state with error
    mock_runner.run.return_value = AgentState(
        scratchpad="User: Test\nError occurred",
        error="Max iterations reached",
        step_count=5
    )

    response = client.post(
        "/api/agent/run",
        json={"user_input": "Test"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["final_answer"] is None
    assert data["error"] == "Max iterations reached"
    assert data["steps"] == 5


# ==================== UNHAPPY PATH TESTS ====================

def test_agent_run_missing_user_input_field(client):
    """Test: Request missing 'user_input' field returns 422."""
    response = client.post(
        "/api/agent/run",
        json={}  # Empty payload
    )

    assert response.status_code == 422
    data = response.json()

    # FastAPI validation error
    assert "detail" in data
    assert any("user_input" in str(error) for error in data["detail"])


def test_agent_run_with_null_user_input(client):
    """Test: user_input=null returns 422."""
    response = client.post(
        "/api/agent/run",
        json={"user_input": None}
    )

    assert response.status_code == 422


def test_agent_run_with_wrong_field_type(client):
    """Test: user_input as number instead of string returns 422."""
    response = client.post(
        "/api/agent/run",
        json={"user_input": 12345}  # Should be string
    )

    assert response.status_code == 422


def test_agent_run_with_empty_string(client, mock_runner):
    """Test: Empty string user_input is allowed (edge case)."""
    response = client.post(
        "/api/agent/run",
        json={"user_input": ""}
    )

    # Empty string is valid (might be intentional)
    assert response.status_code == 200
    mock_runner.run.assert_awaited_once()


def test_agent_run_with_extra_fields_ignored(client, mock_runner):
    """Test: Extra fields in request are ignored."""
    response = client.post(
        "/api/agent/run",
        json={
            "user_input": "Test",
            "extra_field": "ignored",
            "another_field": 123
        }
    )

    # Should succeed and ignore extra fields
    assert response.status_code == 200
    mock_runner.run.assert_awaited_once()


def test_agent_run_with_invalid_json(client):
    """Test: Invalid JSON returns 422."""
    response = client.post(
        "/api/agent/run",
        data="not valid json",  # Not JSON
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422


def test_agent_run_with_wrong_content_type(client):
    """Test: Wrong Content-Type returns 422."""
    response = client.post(
        "/api/agent/run",
        data="user_input=test",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 422

# ==================== EDGE CASES ====================

def test_health_endpoint_accepts_no_body(client):
    """Test: /api/health works without request body."""
    response = client.get("/api/health")
    assert response.status_code == 200

def test_agent_run_preserves_all_state_fields(client, mock_runner):
    """Test: Response includes all expected fields."""
    mock_runner.run.return_value = AgentState(
        messages=[{"role": "user", "content": "Test"}],
        scratchpad="Full scratchpad here",
        final_answer="Answer",
        error=None,
        step_count=3
    )

    response = client.post(
        "/api/agent/run",
        json={"user_input": "Test"}
    )

    data = response.json()

    # Verify all fields present
    assert "final_answer" in data
    assert "scratchpad" in data
    assert "error" in data
    assert "steps" in data

    # Verify values
    assert data["final_answer"] == "Answer"
    assert data["scratchpad"] == "Full scratchpad here"
    assert data["error"] is None
    assert data["steps"] == 3


def test_agent_run_with_unicode_input(client, mock_runner):
    """Test: Endpoint handles Unicode characters."""
    unicode_input = "Hello 你好 مرحبا שלום"

    response = client.post(
        "/api/agent/run",
        json={"user_input": unicode_input}
    )

    assert response.status_code == 200

    # Verify Unicode preserved
    call_args = mock_runner.run.call_args
    initial_state = call_args[0][0]
    assert unicode_input in initial_state.messages[0]["content"]


def test_agent_run_response_matches_schema(client, mock_runner):
    """Test: Response strictly matches AgentRunResponse schema."""
    response = client.post(
        "/api/agent/run",
        json={"user_input": "Test"}
    )

    data = response.json()

    # Exact fields, no more, no less
    assert set(data.keys()) == {"final_answer", "scratchpad", "error", "steps"}

    # Correct types
    assert isinstance(data["final_answer"], (str, type(None)))
    assert isinstance(data["scratchpad"], str)
    assert isinstance(data["error"], (str, type(None)))
    assert isinstance(data["steps"], int)
