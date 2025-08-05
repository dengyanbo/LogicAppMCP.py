"""
Logic App Consumption Package

Contains functionality specific to Logic App Consumption (serverless) plans.
"""

from .client import ConsumptionLogicAppClient
from .mcp_handler import ConsumptionMCPHandler

__all__ = ["ConsumptionLogicAppClient", "ConsumptionMCPHandler"]