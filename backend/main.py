"""
Composition root - wires all dependencies and starts the FastAPI server.
No business logic, only assembly.
"""
import httpx
import uvicorn
from app.agent.react import ReActAgent
from app.core.config import settings
from app.core.logging import setup_logging
from app.interfaces.web import create_app
from app.llm.groq import GroqLLM
from app.services.runner import AgentRunner
from app.tools.implementations.fetcher import FetcherTool
from app.tools.implementations.parser import ParserTool
from app.tools.implementations.scraper import BrowserManager, ScraperTool
from app.tools.registry import ToolRegistry
from fastapi import FastAPI


def bootstrap() -> FastAPI:
    # 1. Configuration
    config = settings

    # 2. Logging
    setup_logging(config.log_level)

    # 3. Shared HTTP client for tools
    http_client = httpx.AsyncClient(
        timeout=30.0, follow_redirects=True, limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )

    # 4. LLM
    llm_client = GroqLLM(api_key=config.groq_api_key, model=config.groq_model)

    # 5. Tools registry
    registry = ToolRegistry()
    registry.register(FetcherTool(http_client))
    registry.register(ScraperTool(http_client))
    registry.register(ParserTool())

    # 6. Agent
    agent = ReActAgent(llm_client, registry)

    # 7. Runner
    runner = AgentRunner(agent, max_iterations=config.max_iterations)

    # 8. Application FastAPI
    app = create_app(runner)

    # 9. Close event for Playwright browser
    async def shutdown_event():
        await BrowserManager().close()

    app.add_event_handler("shutdown", shutdown_event)

    return app


if __name__ == "__main__":
    app = bootstrap()
    uvicorn.run(app, host="0.0.0.0", port=8000)
