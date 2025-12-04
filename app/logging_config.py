"""Logging configuration for the Logic App MCP server."""

import logging
import logging.config

from .config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
ACCESS_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(client_addr)s - \"%(request_line)s\" %(status_code)s"


def get_logging_config() -> dict:
    """Return dictConfig for application and Uvicorn loggers."""
    level = settings.LOG_LEVEL.upper()
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": LOG_FORMAT,
            },
            "access": {
                "format": ACCESS_LOG_FORMAT,
            },
            "uvicorn": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": LOG_FORMAT,
                "use_colors": False,
            },
            "uvicorn_access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": ACCESS_LOG_FORMAT,
                "use_colors": False,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": level,
            },
            "uvicorn": {
                "class": "logging.StreamHandler",
                "formatter": "uvicorn",
            },
            "uvicorn_access": {
                "class": "logging.StreamHandler",
                "formatter": "uvicorn_access",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["uvicorn"], "level": level, "propagate": False},
            "uvicorn.error": {"handlers": ["uvicorn"], "level": level, "propagate": False},
            "uvicorn.access": {"handlers": ["uvicorn_access"], "level": level, "propagate": False},
            "app": {"handlers": ["console"], "level": level, "propagate": False},
        },
        "root": {
            "handlers": ["console"],
            "level": level,
        },
    }


def configure_logging() -> None:
    """Configure logging for the application."""
    logging.config.dictConfig(get_logging_config())
