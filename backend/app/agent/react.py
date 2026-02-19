"""
ReAct Agent with optimized prompting, intelligent termination,
language detection, enhanced loop detection, and structured logging.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Set, Tuple

from app.agent.base import Agent
from app.agent.state import AgentState
from app.core.config import settings
from app.llm.base import LLMClient
from app.tools.registry import ToolRegistry
from langdetect import detect

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """Enhanced execution tracking for intelligent decision-making."""

    action_history: list[Tuple[str, str]] = field(default_factory=list)  # (action, input_hash)
    url_attempts: Set[str] = field(default_factory=set)
    failure_count: int = 0

    def record_action(self, action: str, action_input: str, failed: bool = False):
        """Record action with input hash to detect exact repeats."""
        input_hash = self._hash_input(action_input) if action in ["scraper", "fetcher"] else ""
        self.action_history.append((action, input_hash))
        if action in ["scraper", "fetcher"] and action_input:
            self.url_attempts.add(action_input.strip().lower())
        if failed:
            self.failure_count += 1

    def is_stuck(self) -> bool:
        """Detect if agent is stuck: same (action, input) twice in a row."""
        if len(self.action_history) < 2:
            return False
        return self.action_history[-1] == self.action_history[-2]

    def should_give_up(self) -> bool:
        """Determine if too many failures occurred."""
        return self.failure_count >= 2

    @staticmethod
    def _hash_input(s: str) -> str:
        """Simple hash to compare inputs (avoid storing full strings)."""
        return str(hash(s)) if s else ""


class ReActAgent(Agent):
    """
    Production ReAct agent with:
    - Intelligent scraping with JS support
    - Optimized few-shot prompting
    - Language detection for summaries
    - Enhanced loop detection
    - Graceful error handling with logging
    """

    def __init__(self, llm: LLMClient, tool_registry: ToolRegistry):
        super().__init__(llm, tool_registry)
        self._metrics = ExecutionMetrics()
        self._max_iterations = settings.max_iterations

    async def step(self, state: AgentState) -> AgentState:
        """Execute one reasoning iteration with full error handling."""
        if state.final_answer or state.error:
            return state

        # ---------- THINK ----------
        prompt = self._build_optimized_prompt(state)
        try:
            llm_response = await self.llm.generate(prompt)
            logger.debug(f"LLM response: {llm_response[:200]}...")
        except Exception as e:
            logger.exception("LLM service error")
            return self._create_terminal_state(
                state,
                error_msg=f"LLM service unavailable: {str(e)}",
                user_msg="🔴 The AI service is temporarily unavailable. Please try again in a moment.",
            )

        # ---------- PARSE ----------
        action, action_input, thought = self._parse_llm_response(llm_response)

        scratchpad = state.scratchpad + (
            f"\n\n{'='*50}\n"
            f"STEP {state.step_count + 1}\n"
            f"{'='*50}\n"
            f"💭 Thought: {thought}\n"
            f"🎯 Action: {action}\n"
            f"📝 Input: {action_input}"
        )

        if action == "Final Answer":
            return state.model_copy(
                scratchpad=scratchpad,
                final_answer=action_input,
                step_count=state.step_count + 1,
            )

        # ---------- LOOP DETECTION ----------
        if self._metrics.is_stuck():
            return self._create_terminal_state(
                state,
                error_msg=f"Stuck: repeated '{action}' with same input",
                user_msg="⚠️ I'm having difficulty accessing this content. The website may be blocking automated access or requires special authentication.",
            )

        if self._metrics.should_give_up():
            return self._create_terminal_state(
                state,
                error_msg="Too many failures",
                user_msg="❌ Multiple attempts failed. This website may be inaccessible or requires manual intervention.",
            )

        # ---------- EXECUTE TOOL ----------
        tool = self.tool_registry.get(action)
        if not tool:
            return self._create_terminal_state(
                state,
                error_msg=f"Unknown tool requested: {action}",
                user_msg=f"⚙️ Internal error: Invalid tool '{action}'",
            )

        try:
            result = await tool.execute(action_input)
            action_failed = self._is_error_result(result)
            self._metrics.record_action(action, action_input, failed=action_failed)
        except Exception as e:
            result = f"Tool execution error: {str(e)}"
            self._metrics.record_action(action, action_input, failed=True)

        # ---------- OBSERVE ----------
        if len(result) > 10000:
            result = result[:10000] + "\n\n... (remaining content truncated)"

        observation = f"\n📊 Result: {result}"
        final_scratchpad = scratchpad + observation

        # ---------- SMART TERMINATION ----------
        if action in ["scraper", "fetcher"]:
            return await self._evaluate_and_terminate(state, final_scratchpad, result, action_input)

        return state.model_copy(
            scratchpad=final_scratchpad,
            step_count=state.step_count + 1,
        )

    async def _evaluate_and_terminate(self, state: AgentState, scratchpad: str, result: str, url: str) -> AgentState:
        """Intelligent evaluation with automatic summarization and language detection."""
        if self._is_error_result(result):
            return state.model_copy(
                scratchpad=scratchpad,
                final_answer=f"❌ Failed to access content:\n\n{result}",
                step_count=state.step_count + 1,
            )

        clean_result = result.strip()
        word_count = len(clean_result.split())

        # Detect if user wants a summary
        user_request = state.messages[0].get("content", "").lower() if state.messages else ""
        wants_summary = any(
            kw in user_request
            for kw in [
                "resume",
                "resumen",
                "resumir",
                "summarize",
                "summary",
                "short",
                "brief",
                "corto",
                "breve",
                "tldr",
            ]
        )

        # Language detection for summary (if available)
        target_lang = None
        if wants_summary and detect and user_request:
            try:
                target_lang = detect(user_request)
                logger.info(f"Detected user language: {target_lang}")
            except Exception:
                pass

        min_words = 10
        if word_count < min_words:
            return state.model_copy(
                scratchpad=scratchpad,
                final_answer=(
                    f"❌ **Unable to extract meaningful content from {url}**\n\n"
                    f'Retrieved only: "{clean_result[:100]}..."\n\n'
                    f"**Possible reasons:**\n"
                    f"• Heavy JavaScript rendering\n"
                    f"• Authentication required\n"
                    f"• Bot detection blocking access"
                ),
                step_count=state.step_count + 1,
            )

        if wants_summary:
            try:
                content_for_summary = clean_result[:120000] if len(clean_result) > 120000 else clean_result
                lang_instruction = (
                    f" - Write in {target_lang}"
                    if target_lang
                    else " - Write in the same language as the user's request"
                )
                summary_prompt = f"""You are a professional summarizer. Create a concise, well-structured summary.

                CONTENT TO SUMMARIZE:
                {content_for_summary}

                INSTRUCTIONS:
                {lang_instruction}
                - Focus on the most important information
                - Be clear and direct
                - No markdown, just plain text

                SUMMARY:"""

                summary = await self.llm.generate(summary_prompt)
                summary = summary.strip()
                return state.model_copy(
                    scratchpad=scratchpad,
                    final_answer=f"📝 **Summary:**\n\n{summary}",
                    step_count=state.step_count + 1,
                )
            except Exception as e:
                logger.warning(f"Summarization failed: {e}")
                return state.model_copy(
                    scratchpad=scratchpad,
                    final_answer=(
                        f"⚠️ Could not generate summary due to: {str(e)}\n\n"
                        f"**Here's the extracted content:**\n\n{clean_result[:1000]}..."
                    ),
                    step_count=state.step_count + 1,
                )

        return state.model_copy(
            scratchpad=scratchpad,
            final_answer=f"✅ **Successfully scraped content:**\n\n{clean_result}",
            step_count=state.step_count + 1,
        )

    def _build_optimized_prompt(self, state: AgentState) -> str:
        """Few-shot prompt with strict JSON instruction."""
        tools_list = list(self.tool_registry.list_all().items())
        tools_desc = "\n".join(f"  {i+1}. **{name}**: {tool.description}" for i, (name, tool) in enumerate(tools_list))

        user_request = state.messages[0].get("content", "") if state.messages else ""

        context_note = (
            "**Previous attempts recorded below.** Learn from any failures and try a different approach if needed."
            if state.scratchpad.strip()
            else "**First attempt.** Choose the best tool for the task."
        )

        # Few-shot examples
        examples = """
        **Example 1: Scraping a URL**
        Input: "scrape https://example.com"
        Output: {"thought": "I need to extract content from this URL", "action": "scraper", "action_input": "https://example.com"}

        **Example 2: Summarize a URL**
        Input: "summarize https://news.com/article"
        Output: {"thought": "The user wants a summary, so I'll scrape and let the system summarize", "action": "scraper", "action_input": "https://news.com/article"}

        **Example 3: Final answer**
        Input: "What is 2+2?"
        Output: {"thought": "This is a simple question, I can answer directly", "action": "Final Answer", "action_input": "4"}

        """

        return f"""You are an AI web scraping assistant. Your job is to help users extract information from websites.

        🛠️ **AVAILABLE TOOLS:**
        {tools_desc}

        📋 **USER REQUEST:**
        "{user_request}"

        📝 **CONTEXT:** {context_note}

        {f"**WORK LOG:**{state.scratchpad}" if state.scratchpad.strip() else ""}

        ---

        ⚡ **YOUR TASK:**
        1. Read the user's request carefully
        2. Select the most appropriate tool
        3. Provide the exact input needed (for URLs, include the full URL)

        🎯 **DECISION RULES:**
        - For "scrape [url]" → use **scraper** tool to get full content
        - For "resume/resumen/summarize [url]" → use **scraper** tool (I will auto-summarize the result)
        - The scraper handles JavaScript sites automatically
        - After scraping, you will receive either full content or a summary based on user's request
        - DO NOT call the same tool twice with the same input
        - If previous attempt failed, the site may not be accessible

        📤 **RESPONSE FORMAT** (JSON only, no markdown, no extra text):
        {{"thought": "I need to scrape the website to extract the content", "action": "scraper", "action_input": "https://example.com"}}

        **Valid actions:** {', '.join(name for name, _ in tools_list)}, Final Answer

        **EXAMPLES:**
        {examples}

        🤖 **Your response (JSON only):**"""

    def _parse_llm_response(self, response: str) -> Tuple[str, str, str]:
        """Robust JSON extraction with comprehensive fallback."""
        response = response.strip()
        response = re.sub(r"```json\s*", "", response)
        response = re.sub(r"```\s*", "", response)

        json_pattern = r'\{[^{}]*"thought"[^{}]*"action"[^{}]*"action_input"[^{}]*\}'
        match = re.search(json_pattern, response, re.DOTALL | re.IGNORECASE)

        if not match:
            logger.warning("No JSON found in LLM response, using fallback.")
            return "Final Answer", response, "No structured response"

        try:
            data = json.loads(match.group(0))
            thought = str(data.get("thought", "")).strip()
            action = str(data.get("action", "")).strip()
            action_input = str(data.get("action_input", "")).strip()

            tool_mapping = {tool.name.lower(): tool.name for tool in self.tool_registry.list_all().values()}
            tool_mapping.update(
                {"final answer": "Final Answer", "finalanswer": "Final Answer", "finish": "Final Answer"}
            )

            normalized = tool_mapping.get(action.lower(), "Final Answer")
            return normalized, action_input, thought

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"JSON parsing failed: {e}")
            return "Final Answer", response, "JSON parsing failed"

    def _is_error_result(self, result: str) -> bool:
        error_markers = [
            "Error:",
            "HTTP Error",
            "Failed to",
            "Unable to",
            "Connection refused",
            "Timeout",
            "Not Found",
            "Forbidden",
        ]
        return any(marker in result for marker in error_markers)

    def _create_terminal_state(self, state: AgentState, error_msg: str, user_msg: str) -> AgentState:
        return state.model_copy(
            scratchpad=state.scratchpad + f"\n\n❌ **ERROR:** {error_msg}",
            error=error_msg,
            final_answer=user_msg,
            step_count=state.step_count + 1,
        )
