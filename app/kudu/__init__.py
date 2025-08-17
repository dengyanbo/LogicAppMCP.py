"""
Kudu MCP Package

Provides Model Context Protocol (MCP) interface for Azure Kudu services,
enabling management and debugging of Logic App Standard deployments through
the Kudu REST API.
"""

from .client import KuduClient
from .mcp_handler import KuduMCPHandler

__all__ = [
    "KuduClient",
    "KuduMCPHandler",
]
