"""
Logging configuration using structlog for structured logs.
"""
import logging

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog and standard logging."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    # Set global log level
    logging.basicConfig(level=log_level)
