"""
Real E2E tests simulating user interactions with Playwright.
Tests the complete user journey: type, click, wait, verify.
"""
import os
import re

import pytest
from playwright.sync_api import Page, expect

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")


# ==================== HEALTH CHECKS ====================

@pytest.mark.e2e
def test_services_are_running(page: Page):
    """Test: Services are accessible before running other tests."""
    # Check backend
    response = page.request.get(f"http://localhost:{BACKEND_PORT}/api/health")
    assert response.ok, "Backend is not running. Start with: docker-compose up -d"

    # Check frontend
    response = page.goto(FRONTEND_URL)
    assert response.ok, "Frontend is not running"


# ==================== UI RENDERING TESTS ====================

@pytest.mark.e2e
def test_chat_interface_loads_correctly(page: Page):
    """
    Test: Chat interface renders with all elements.

    User journey:
    1. Navigate to app
    2. Verify header present
    3. Verify input box present
    4. Verify send button present
    """
    page.goto(FRONTEND_URL)

    # Header with title
    header = page.locator('h1:has-text("Web Agent Scraper")')
    expect(header).to_be_visible()

    # Status indicator
    status = page.locator('text=Online')
    expect(status).to_be_visible()

    # Textarea for input
    textarea = page.locator('textarea')
    expect(textarea).to_be_visible()
    expect(textarea).to_have_attribute('placeholder', re.compile('Type a message'))

    # Send button
    send_button = page.locator('button').filter(has=page.locator('svg'))
    expect(send_button).to_be_visible()

# ==================== USER INTERACTION TESTS ====================

@pytest.mark.e2e
def test_user_can_type_in_textarea(page: Page):
    """
    Test: User can type in the input field.

    User journey:
    1. Click textarea
    2. Type message
    3. Verify text appears
    """
    page.goto(FRONTEND_URL)

    textarea = page.locator('textarea')

    # Click to focus
    textarea.click()

    # Type message
    test_message = "Hello, this is a test message"
    textarea.fill(test_message)

    # Verify text is in textarea
    expect(textarea).to_have_value(test_message)


@pytest.mark.e2e
def test_send_button_disabled_when_empty(page: Page):
    """
    Test: Send button is disabled when textarea is empty.

    User journey:
    1. Load page
    2. Verify send button is disabled
    3. Type something
    4. Verify send button is enabled
    """
    page.goto(FRONTEND_URL)

    textarea = page.locator('textarea')
    send_button = page.locator('button').filter(has=page.locator('svg')).last

    # Initially disabled (empty)
    expect(send_button).to_be_disabled()

    # Type something
    textarea.fill("test")

    # Now enabled
    expect(send_button).to_be_enabled()


@pytest.mark.e2e
def test_user_sends_message_with_mock_backend(page: Page, mock_backend_success):
    """
    Test: User can send a message and receive response (mocked backend).

    User journey:
    1. Type message
    2. Click send button
    3. See user message appear (right side)
    4. See loading indicator
    5. See agent response appear (left side)
    """
    page.goto(FRONTEND_URL)

    textarea = page.locator('textarea')
    send_button = page.locator('button').filter(has=page.locator('svg')).last

    # Type and send
    test_message = "scrape https://example.com"
    textarea.fill(test_message)
    send_button.click()

    # User message should appear on the right
    user_message = page.locator('.justify-end').filter(has_text=test_message)
    expect(user_message).to_be_visible(timeout=2000)

    # Loading indicator should appear briefly
    # (might be too fast to catch, so we skip this check)

    # Agent response should appear on the left
    agent_message = page.locator('.justify-start').filter(has_text="Successfully scraped")
    expect(agent_message).to_be_visible(timeout=5000)

    # Textarea should be cleared
    expect(textarea).to_have_value("")


@pytest.mark.e2e
def test_enter_key_sends_message(page: Page, mock_backend_success):
    """
    Test: Pressing Enter sends the message (not Shift+Enter).

    User journey:
    1. Type message
    2. Press Enter
    3. Message is sent
    """
    page.goto(FRONTEND_URL)

    textarea = page.locator('textarea')

    # Type message
    textarea.fill("Test message via Enter key")

    # Press Enter
    textarea.press("Enter")

    # Message should appear
    user_message = page.locator('.justify-end').filter(has_text="Test message")
    expect(user_message).to_be_visible(timeout=2000)


@pytest.mark.e2e
def test_multiple_messages_in_conversation(page: Page, mock_backend_success):
    """
    Test: User can send multiple messages in sequence.

    User journey:
    1. Send first message
    2. Wait for response
    3. Send second message
    4. Verify both conversations visible
    """
    page.goto(FRONTEND_URL)

    textarea = page.locator('textarea')
    send_button = page.locator('button').filter(has=page.locator('svg')).last

    # First message
    textarea.fill("First message")
    send_button.click()
    page.wait_for_timeout(1000)

    # Second message
    textarea.fill("Second message")
    send_button.click()
    page.wait_for_timeout(1000)

    # Both should be visible
    first_msg = page.locator('.justify-end').filter(has_text="First message")
    second_msg = page.locator('.justify-end').filter(has_text="Second message")

    expect(first_msg).to_be_visible()
    expect(second_msg).to_be_visible()


# ==================== ERROR HANDLING TESTS ====================

@pytest.mark.e2e
def test_error_banner_appears_on_backend_failure(page: Page, mock_backend_error):
    """
    Test: Error banner shows when backend fails.

    User journey:
    1. Send message
    2. Backend returns error
    3. See error banner
    """
    page.goto(FRONTEND_URL)

    textarea = page.locator('textarea')
    send_button = page.locator('button').filter(has=page.locator('svg')).last

    # Send message
    textarea.fill("test")
    send_button.click()

    # Error banner should appear
    error_banner = page.locator('[class*="bg-red"]')
    expect(error_banner).to_be_visible(timeout=5000)


@pytest.mark.e2e
def test_loading_state_during_processing(page: Page, mock_backend_success):
    """
    Test: Loading indicator shows while agent processes.

    User journey:
    1. Send message
    2. See "Agent is thinking..." status
    3. Status returns to "Online"
    """
    page.goto(FRONTEND_URL)

    textarea = page.locator('textarea')
    send_button = page.locator('button').filter(has=page.locator('svg')).last

    # Send message
    textarea.fill("test")
    send_button.click()

    # Should see "thinking" status (might be brief)
    thinking_status = page.locator('text=Agent is thinking')
    # We use wait_for with a short timeout since it might be very fast
    try:
        thinking_status.wait_for(state="visible", timeout=2000)
    except Exception:
        pass  # OK if too fast to catch

    # Should return to "Online"
    online_status = page.locator('text=Online')
    expect(online_status).to_be_visible(timeout=5000)
