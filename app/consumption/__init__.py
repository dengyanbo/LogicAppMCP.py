"""
Logic App Consumption Package

A comprehensive Model Context Protocol (MCP) handler for Azure Logic Apps Consumption tier.

This package provides full programmatic access to the Microsoft Logic Apps REST API (2016-06-01)
through the Model Context Protocol, enabling developers to manage workflows, runs, triggers,
versions, and integration accounts.

Features:
- 38 API Operations across 7 categories
- Complete Microsoft REST API coverage
- MCP 2024-11-05 compliant
- Async/await support
- Comprehensive error handling
- Azure SDK integration

Classes:
- ConsumptionLogicAppClient: Azure Logic Apps client implementation
- ConsumptionMCPHandler: Main MCP protocol handler

Example:
    from app.consumption import ConsumptionMCPHandler
    
    handler = ConsumptionMCPHandler()
    response = await handler.handle_request({
        "method": "tools/call",
        "params": {
            "name": "list_consumption_logic_apps",
            "arguments": {}
        }
    })
"""

from .client import ConsumptionLogicAppClient
from .mcp_handler import ConsumptionMCPHandler

__version__ = "1.0.0"
__api_version__ = "2016-06-01"
__mcp_version__ = "2024-11-05"

__all__ = [
    "ConsumptionLogicAppClient",
    "ConsumptionMCPHandler",
    "__version__",
    "__api_version__",
    "__mcp_version__"
]