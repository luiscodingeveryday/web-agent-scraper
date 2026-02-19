"""
Concrete implementation for Groq Cloud API.
Free and fast alternative to Ollama.
"""
import httpx
from app.core.exceptions import LLMError
from app.llm.base import LLMClient


class GroqLLM(LLMClient):
    """Adapter for Groq's cloud API."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate(self, prompt: str) -> str:
        """
        Send a prompt to Groq and return the response content.
        """
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, headers=headers, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise LLMError(f"Groq API call failed: {str(e)}") from e
