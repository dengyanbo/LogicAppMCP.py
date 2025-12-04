"""Helpers for resilient TLS certificate configuration."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import certifi

logger = logging.getLogger(__name__)


def ensure_requests_ca_bundle() -> Path:
    """Ensure ``requests`` can find a valid CA bundle.

    Some environments inject ``SSL_CERT_FILE``/``REQUESTS_CA_BUNDLE`` values that point
    to non-existent files, causing ``requests`` to raise ``FileNotFoundError`` during
    import. This function verifies the configured paths and, if they are missing,
    falls back to ``certifi``'s bundle so the application can start cleanly.
    """

    env_vars = ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE")

    for var in env_vars:
        configured = os.environ.get(var)
        if configured and Path(configured).is_file():
            return Path(configured)

    fallback = Path(certifi.where())
    for var in env_vars:
        os.environ[var] = str(fallback)

    logger.info("Configured CA bundle at %s for requests", fallback)
    return fallback

