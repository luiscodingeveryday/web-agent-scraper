"""
Centralised configuration using Pydantic settings.
No hardcoded strings elsewhere.
"""
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Groq configuration
    groq_api_key: str = Field(alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # Agent settings
    max_iterations: int = Field(alias="MAX_ITERATIONS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Scraper settings (with defaults, can be overridden in .env)
    scraper_max_length: int = Field(default=15000, alias="SCRAPER_MAX_LENGTH")
    scraper_min_words_quality: int = Field(default=50, alias="SCRAPER_MIN_WORDS_QUALITY")
    scraper_min_words_poor: int = Field(default=10, alias="SCRAPER_MIN_WORDS_POOR")
    scraper_timeout: int = Field(default=30, alias="SCRAPER_TIMEOUT")
    scraper_retry_attempts: int = Field(default=3, alias="SCRAPER_RETRY_ATTEMPTS")
    scraper_polite_delay: float = Field(default=1.0, alias="SCRAPER_POLITE_DELAY")

    # User agents (hardcoded here)
    user_agents: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")


settings = Settings()
