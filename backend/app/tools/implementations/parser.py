"""
Tool: Parser – extracts specific information from text using regex.
Demonstrates a simple transformation tool.
"""
import re

from app.tools.base import Tool


class ParserTool(Tool):
    """Extract email addresses or URLs from a block of text."""

    @property
    def name(self) -> str:
        return "parser"

    @property
    def description(self) -> str:
        return "Extract all email addresses or URLs from text. Input: 'emails' or 'urls' followed by the text."

    async def execute(self, input_data: str) -> str:
        """Parse based on command prefix."""
        lines = input_data.strip().split("\n", 1)
        command = lines[0].lower()
        text = lines[1] if len(lines) > 1 else ""

        if command == "emails":
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
            return ", ".join(emails) if emails else "No emails found."
        elif command == "urls":
            urls = re.findall(r"https?://[^\s]+", text)
            return ", ".join(urls) if urls else "No URLs found."
        else:
            return f"Unknown parser command: {command}. Use 'emails' or 'urls'."
