"""
Consumption MCP Handler

Handles MCP requests specific to Logic App Consumption (serverless) plans.
"""

import json
from typing import Dict, Any, List, Optional
from .client import ConsumptionLogicAppClient
from ..config import settings


class ConsumptionMCPHandler:
    """MCP Protocol Request Handler for Logic App Consumption"""
    
    def __init__(self):
        self.logicapp_client = ConsumptionLogicAppClient()
        self.server_info = {
            "name": f"{settings.MCP_SERVER_NAME}-consumption",
            "version": settings.MCP_SERVER_VERSION,
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": False,
                "logging": True
            }
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                response = await self._handle_initialize(params)
            elif method == "tools/list":
                response = await self._handle_tools_list()
            elif method == "tools/call":
                response = await self._handle_tools_call(params)
            elif method == "resources/list":
                response = await self._handle_resources_list()
            elif method == "resources/read":
                response = await self._handle_resources_read(params)
            else:
                response = {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # Add request ID to response
            if request_id:
                response["id"] = request_id
                
            return response
        
        except Exception as e:
            return {
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": self.server_info,
                "capabilities": self.server_info["capabilities"]
            }
        }
    
    async def _handle_tools_list(self) -> Dict[str, Any]:
        """Return list of available tools for Consumption Logic Apps"""
        tools = [
            {
                "name": "list_consumption_logic_apps",
                "description": "List all Logic App Consumption instances",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_consumption_logic_app",
                "description": "Get detailed information for a specific Consumption Logic App",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "create_consumption_logic_app",
                "description": "Create a new Consumption Logic App",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "definition": {
                            "type": "object",
                            "description": "Logic App definition (JSON format)"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Workflow parameters (optional)"
                        },
                        "access_control": {
                            "type": "object",
                            "description": "Access control configuration (optional)"
                        }
                    },
                    "required": ["workflow_name", "definition"]
                }
            },
            {
                "name": "trigger_consumption_logic_app",
                "description": "Trigger Consumption Logic App execution",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "trigger_name": {
                            "type": "string",
                            "description": "Trigger name (default is manual)",
                            "default": "manual"
                        },
                        "payload": {
                            "type": "object",
                            "description": "Payload to send with trigger"
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "get_consumption_run_history",
                "description": "Get Consumption Logic App run history",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Limit on number of records returned",
                            "default": 10
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "get_consumption_metrics",
                "description": "Get Consumption-specific metrics and billing information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to analyze",
                            "default": 7
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "configure_http_trigger",
                "description": "Configure HTTP trigger for Consumption Logic App",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "trigger_config": {
                            "type": "object",
                            "description": "HTTP trigger configuration",
                            "properties": {
                                "method": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "HTTP methods allowed"
                                },
                                "schema": {
                                    "type": "object",
                                    "description": "Request schema"
                                },
                                "relative_path": {
                                    "type": "string",
                                    "description": "Relative path for the trigger"
                                }
                            }
                        }
                    },
                    "required": ["workflow_name", "trigger_config"]
                }
            }
        ]
        
        return {"result": {"tools": tools}}
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls for Consumption Logic Apps"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "list_consumption_logic_apps":
            result = await self.logicapp_client.list_logic_apps()
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            }
        
        elif tool_name == "get_consumption_logic_app":
            workflow_name = arguments.get("workflow_name")
            result = await self.logicapp_client.get_logic_app(workflow_name)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            }
        
        elif tool_name == "create_consumption_logic_app":
            workflow_name = arguments.get("workflow_name")
            definition = arguments.get("definition")
            kwargs = {k: v for k, v in arguments.items() if k not in ["workflow_name", "definition"]}
            result = await self.logicapp_client.create_logic_app(workflow_name, definition, **kwargs)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Consumption Logic App '{workflow_name}' created: {result}"
                        }
                    ]
                }
            }
        
        elif tool_name == "trigger_consumption_logic_app":
            workflow_name = arguments.get("workflow_name")
            trigger_name = arguments.get("trigger_name", "manual")
            kwargs = {k: v for k, v in arguments.items() if k not in ["workflow_name", "trigger_name"]}
            result = await self.logicapp_client.trigger_logic_app(workflow_name, trigger_name, **kwargs)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            }
        
        elif tool_name == "get_consumption_run_history":
            workflow_name = arguments.get("workflow_name")
            limit = arguments.get("limit", 10)
            result = await self.logicapp_client.get_run_history(workflow_name, limit)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            }
        
        elif tool_name == "get_consumption_metrics":
            workflow_name = arguments.get("workflow_name")
            days = arguments.get("days", 7)
            result = await self.logicapp_client.get_consumption_metrics(workflow_name, days)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            }
        
        elif tool_name == "configure_http_trigger":
            workflow_name = arguments.get("workflow_name")
            trigger_config = arguments.get("trigger_config")
            result = await self.logicapp_client.configure_http_trigger(workflow_name, trigger_config)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"HTTP trigger configured for '{workflow_name}': {result}"
                        }
                    ]
                }
            }
        
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
    
    async def _handle_resources_list(self) -> Dict[str, Any]:
        """Return list of available resources for Consumption Logic Apps"""
        resources = [
            {
                "uri": "logicapp://consumption/workflows",
                "name": "Consumption Logic Apps List",
                "description": "All Consumption Logic Apps in the current subscription",
                "mimeType": "application/json"
            }
        ]
        
        return {"result": {"resources": resources}}
    
    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read resource content for Consumption Logic Apps"""
        uri = params.get("uri")
        
        if uri == "logicapp://consumption/workflows":
            workflows = await self.logicapp_client.list_logic_apps()
            return {
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(workflows, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            }
        else:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Unknown resource URI: {uri}"
                }
            }