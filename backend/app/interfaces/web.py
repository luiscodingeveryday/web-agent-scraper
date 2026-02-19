"""
HTTP translation layer – only request/response handling.
No business logic, no direct imports from agent or tools.
"""
from app.agent.state import AgentState
from app.services.runner import AgentRunner
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ---------- Request/Response Schemas ----------
class AgentRunRequest(BaseModel):
    user_input: str


class AgentRunResponse(BaseModel):
    final_answer: str | None
    scratchpad: str
    error: str | None
    steps: int


# ---------- Endpoints ----------
def create_app(runner: AgentRunner) -> FastAPI:
    """Factory to create FastAPI app with dependencies."""

    app = FastAPI(title="Agentic AI Backend")

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store runner in app state for dependency injection
    app.state.runner = runner

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/agent/run", response_model=AgentRunResponse)
    async def run_agent(request: AgentRunRequest) -> AgentRunResponse:
        """
        Execute the agent with the given user input.
        """
        # Build initial state from request
        initial_state = AgentState(
            messages=[{"role": "user", "content": request.user_input}], scratchpad=f"User: {request.user_input}"
        )

        # Run agent
        final_state = await runner.run(initial_state)

        # Translate to response
        return AgentRunResponse(
            final_answer=final_state.final_answer,
            scratchpad=final_state.scratchpad,
            error=final_state.error,
            steps=final_state.step_count,
        )

    return app
