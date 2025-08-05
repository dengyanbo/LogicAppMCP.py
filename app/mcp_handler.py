"""
MCP Request Handler

Handles various Model Context Protocol (MCP) requests, including tool calls, resource access, etc.
"""

import json
from typing import Dict, Any, List, Optional
from .logicapp_client import LogicAppClient
from .config import settings


class MCPHandler:
    """MCP Protocol Request Handler"""
    
    def __init__(self):
        self.logicapp_client = LogicAppClient()
        self.server_info = {
            "name": settings.MCP_SERVER_NAME,
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
        """Return list of available tools"""
        tools = [
            {
                "name": "list_logic_apps",
                "description": "List all Azure Logic Apps",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_logic_app",
                "description": "Get detailed information for a specific Logic App",
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
                "name": "create_logic_app",
                "description": "Create a new Logic App",
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
                        }
                    },
                    "required": ["workflow_name", "definition"]
                }
            },
            {
                "name": "trigger_logic_app",
                "description": "Manually trigger Logic App execution",
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
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "get_run_history",
                "description": "Get Logic App run history",
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
            }
        ]
        
        return {"result": {"tools": tools}}
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "list_logic_apps":
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
        
        elif tool_name == "get_logic_app":
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
        
        elif tool_name == "create_logic_app":
            workflow_name = arguments.get("workflow_name")
            definition = arguments.get("definition")
            result = await self.logicapp_client.create_logic_app(workflow_name, definition)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Logic App '{workflow_name}' created: {result}"
                        }
                    ]
                }
            }
        
        elif tool_name == "trigger_logic_app":
            workflow_name = arguments.get("workflow_name")
            trigger_name = arguments.get("trigger_name", "manual")
            result = await self.logicapp_client.trigger_logic_app(workflow_name, trigger_name)
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
        
        elif tool_name == "get_run_history":
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
        
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
    
    async def _handle_resources_list(self) -> Dict[str, Any]:
        """Return list of available resources"""
        resources = [
            {
                "uri": "logicapp://workflows",
                "name": "Logic Apps List",
                "description": "All Logic Apps in the current subscription",
                "mimeType": "application/json"
            }
        ]
        
        return {"result": {"resources": resources}}
    
    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read resource content"""
        uri = params.get("uri")
        
        if uri == "logicapp://workflows":
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