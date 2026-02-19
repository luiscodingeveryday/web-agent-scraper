"""
E2E test configuration for Playwright.
"""
import pytest
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context."""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configure browser launch."""
    return {
        **browser_type_launch_args,
        "headless": True,
        "slow_mo": 0,      # 500 for debugging
    }


@pytest.fixture
def mock_backend_success(page: Page):
    """Mock backend responses for fast testing."""
    page.route("**/agent/run", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"final_answer": "Successfully scraped content from example.com", "scratchpad": "test", "error": null, "steps": 1}'
    ))


@pytest.fixture
def mock_backend_error(page: Page):
    """Mock backend error response."""
    page.route("**/agent/run", lambda route: route.fulfill(
        status=500,
        content_type="application/json",
        body='{"detail": "Internal server error"}'
    ))
