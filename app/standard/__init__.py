"""
Logic App Standard Package

Contains functionality specific to Logic App Standard (dedicated hosting) plans.
"""

from .client import StandardLogicAppClient
from .mcp_handler import StandardMCPHandler

__all__ = ["StandardLogicAppClient", "StandardMCPHandler"]