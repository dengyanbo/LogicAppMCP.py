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
        self._tools_cache = None
        self._required_by_tool: Dict[str, List[str]] = {}
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            # Basic input validation per MCP 2024-11-05
            if not isinstance(method, str):
                return {
                    "id": request_id,
                    "error": {"code": -32600, "message": "Invalid Request: 'method' must be a string"},
                }
            if method == "initialize":
                response = await self._handle_initialize(params)
            elif method == "tools/list":
                response = await self._handle_tools_list()
            elif method == "tools/call":
                if not isinstance(params, dict):
                    return {"id": request_id, "error": {"code": -32602, "message": "Invalid params"}}
                response = await self._handle_tools_call(params)
            elif method == "resources/list":
                response = await self._handle_resources_list()
            elif method == "resources/read":
                if not isinstance(params, dict):
                    return {"id": request_id, "error": {"code": -32602, "message": "Invalid params"}}
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
            # Workflow Management
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
                "name": "update_consumption_logic_app",
                "description": "Update an existing Consumption Logic App",
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
                        "state": {
                            "type": "string",
                            "enum": ["Enabled", "Disabled"],
                            "description": "Workflow state (optional)"
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "delete_consumption_logic_app",
                "description": "Delete a Consumption Logic App",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App to delete"
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "enable_consumption_logic_app",
                "description": "Enable a Consumption Logic App",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App to enable"
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "disable_consumption_logic_app",
                "description": "Disable a Consumption Logic App",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App to disable"
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "validate_consumption_logic_app",
                "description": "Validate a Consumption Logic App definition",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App (for existing workflow validation)"
                        },
                        "definition": {
                            "type": "object",
                            "description": "Logic App definition to validate"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Workflow parameters (optional)"
                        }
                    },
                    "required": ["definition"]
                }
            },
            {
                "name": "get_logic_app_callback_url",
                "description": "Get the callback URL for a Logic App trigger",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "trigger_name": {
                            "type": "string",
                            "description": "Name of the trigger",
                            "default": "manual"
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "get_logic_app_swagger",
                "description": "Get the OpenAPI/Swagger definition for a Logic App",
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
            
            # Workflow Runs Management
            {
                "name": "list_consumption_workflow_runs",
                "description": "List workflow runs for a Consumption Logic App",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Number of items to return",
                            "default": 30
                        },
                        "filter": {
                            "type": "string",
                            "description": "OData filter expression"
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "get_consumption_workflow_run",
                "description": "Get details for a specific workflow run",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "run_name": {
                            "type": "string",
                            "description": "Name/ID of the workflow run"
                        }
                    },
                    "required": ["workflow_name", "run_name"]
                }
            },
            {
                "name": "cancel_consumption_workflow_run",
                "description": "Cancel a running workflow execution",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "run_name": {
                            "type": "string",
                            "description": "Name/ID of the workflow run to cancel"
                        }
                    },
                    "required": ["workflow_name", "run_name"]
                }
            },
            {
                "name": "resubmit_consumption_workflow_run",
                "description": "Resubmit a failed workflow run",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "run_name": {
                            "type": "string",
                            "description": "Name/ID of the workflow run to resubmit"
                        }
                    },
                    "required": ["workflow_name", "run_name"]
                }
            },
            
            # Workflow Triggers Management
            {
                "name": "list_consumption_workflow_triggers",
                "description": "List triggers for a Consumption Logic App",
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
                "name": "get_consumption_workflow_trigger",
                "description": "Get details for a specific workflow trigger",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "trigger_name": {
                            "type": "string",
                            "description": "Name of the trigger"
                        }
                    },
                    "required": ["workflow_name", "trigger_name"]
                }
            },
            {
                "name": "run_consumption_workflow_trigger",
                "description": "Manually run a workflow trigger",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "trigger_name": {
                            "type": "string",
                            "description": "Name of the trigger"
                        }
                    },
                    "required": ["workflow_name", "trigger_name"]
                }
            },
            {
                "name": "reset_consumption_workflow_trigger",
                "description": "Reset a workflow trigger state",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "trigger_name": {
                            "type": "string",
                            "description": "Name of the trigger"
                        }
                    },
                    "required": ["workflow_name", "trigger_name"]
                }
            },
            {
                "name": "get_trigger_schema",
                "description": "Get the JSON schema for a workflow trigger",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "trigger_name": {
                            "type": "string",
                            "description": "Name of the trigger"
                        }
                    },
                    "required": ["workflow_name", "trigger_name"]
                }
            },
            
            # Workflow Trigger Histories
            {
                "name": "list_trigger_histories",
                "description": "List trigger history for a workflow trigger",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "trigger_name": {
                            "type": "string",
                            "description": "Name of the trigger"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Number of items to return",
                            "default": 30
                        }
                    },
                    "required": ["workflow_name", "trigger_name"]
                }
            },
            {
                "name": "get_trigger_history",
                "description": "Get specific trigger history details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "trigger_name": {
                            "type": "string",
                            "description": "Name of the trigger"
                        },
                        "history_name": {
                            "type": "string",
                            "description": "Name/ID of the trigger history"
                        }
                    },
                    "required": ["workflow_name", "trigger_name", "history_name"]
                }
            },
            
            # Workflow Run Actions
            {
                "name": "list_workflow_run_actions",
                "description": "List actions for a specific workflow run",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "run_name": {
                            "type": "string",
                            "description": "Name/ID of the workflow run"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Number of items to return",
                            "default": 30
                        }
                    },
                    "required": ["workflow_name", "run_name"]
                }
            },
            {
                "name": "get_workflow_run_action",
                "description": "Get details for a specific workflow run action",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "run_name": {
                            "type": "string",
                            "description": "Name/ID of the workflow run"
                        },
                        "action_name": {
                            "type": "string",
                            "description": "Name of the action"
                        }
                    },
                    "required": ["workflow_name", "run_name", "action_name"]
                }
            },
            
            # Workflow Versions
            {
                "name": "list_workflow_versions",
                "description": "List all versions of a workflow",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Number of items to return",
                            "default": 30
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "get_workflow_version",
                "description": "Get details for a specific workflow version",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "version_id": {
                            "type": "string",
                            "description": "Version ID of the workflow"
                        }
                    },
                    "required": ["workflow_name", "version_id"]
                }
            },
            
            # Integration Account Management (Basic Support)
            {
                "name": "list_integration_accounts",
                "description": "List integration accounts in the subscription",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "top": {
                            "type": "integer",
                            "description": "Number of items to return",
                            "default": 30
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_integration_account",
                "description": "Get details for a specific integration account",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "integration_account_name": {
                            "type": "string",
                            "description": "Name of the integration account"
                        }
                    },
                    "required": ["integration_account_name"]
                }
            },
            {
                "name": "create_integration_account",
                "description": "Create a new integration account",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "integration_account_name": {
                            "type": "string",
                            "description": "Name of the integration account"
                        },
                        "sku": {
                            "type": "string",
                            "enum": ["Free", "Standard"],
                            "description": "SKU tier for the integration account",
                            "default": "Free"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location for the integration account"
                        }
                    },
                    "required": ["integration_account_name"]
                }
            },
            {
                "name": "delete_integration_account",
                "description": "Delete an integration account",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "integration_account_name": {
                            "type": "string",
                            "description": "Name of the integration account to delete"
                        }
                    },
                    "required": ["integration_account_name"]
                }
            },
            {
                "name": "list_integration_account_maps",
                "description": "List maps in an integration account",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "integration_account_name": {
                            "type": "string",
                            "description": "Name of the integration account"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Number of items to return",
                            "default": 30
                        }
                    },
                    "required": ["integration_account_name"]
                }
            },
            {
                "name": "list_integration_account_schemas",
                "description": "List schemas in an integration account",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "integration_account_name": {
                            "type": "string",
                            "description": "Name of the integration account"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Number of items to return",
                            "default": 30
                        }
                    },
                    "required": ["integration_account_name"]
                }
            },
            {
                "name": "list_integration_account_partners",
                "description": "List partners in an integration account",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "integration_account_name": {
                            "type": "string",
                            "description": "Name of the integration account"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Number of items to return",
                            "default": 30
                        }
                    },
                    "required": ["integration_account_name"]
                }
            },
            {
                "name": "list_integration_account_agreements",
                "description": "List agreements in an integration account",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "integration_account_name": {
                            "type": "string",
                            "description": "Name of the integration account"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Number of items to return",
                            "default": 30
                        }
                    },
                    "required": ["integration_account_name"]
                }
            },
            {
                "name": "get_integration_account_callback_url",
                "description": "Get callback URL for an integration account",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "integration_account_name": {
                            "type": "string",
                            "description": "Name of the integration account"
                        },
                        "key_type": {
                            "type": "string",
                            "enum": ["Primary", "Secondary"],
                            "description": "Key type for the callback URL",
                            "default": "Primary"
                        }
                    },
                    "required": ["integration_account_name"]
                }
            },
            
            # Legacy/Compatibility APIs
            {
                "name": "trigger_consumption_logic_app",
                "description": "Trigger Consumption Logic App execution (legacy method)",
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
                "description": "Get Consumption Logic App run history (legacy method)",
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
                "description": "Configure HTTP trigger for Consumption Logic App (legacy method)",
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
        # Cache and extract required args for validation
        self._tools_cache = tools
        self._required_by_tool = {}
        for tool in tools:
            name = tool.get("name")
            required = tool.get("inputSchema", {}).get("required", []) or []
            if name:
                self._required_by_tool[name] = required
        return {"result": {"tools": tools}}
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls for Consumption Logic Apps"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            # Ensure we have tool definitions loaded for validation
            if not self._tools_cache:
                await self._handle_tools_list()
            # Validate required args
            missing = [k for k in self._required_by_tool.get(tool_name, []) if k not in arguments or arguments.get(k) in (None, "")]
            if missing:
                return {
                    "error": {
                        "code": -32602,
                        "message": f"Missing required parameter(s) for {tool_name}: {', '.join(missing)}",
                    }
                }
            # Workflow Management APIs
            if tool_name == "list_consumption_logic_apps":
                result = await self.logicapp_client.list_logic_apps()
                return self._format_json_response(result)
            
            elif tool_name == "get_consumption_logic_app":
                workflow_name = arguments.get("workflow_name")
                result = await self.logicapp_client.get_logic_app(workflow_name)
                return self._format_json_response(result)
            
            elif tool_name == "create_consumption_logic_app":
                workflow_name = arguments.get("workflow_name")
                definition = arguments.get("definition")
                kwargs = {k: v for k, v in arguments.items() if k not in ["workflow_name", "definition"]}
                result = await self.logicapp_client.create_logic_app(workflow_name, definition, **kwargs)
                return self._format_text_response(f"Consumption Logic App '{workflow_name}' created: {result}")
            
            elif tool_name == "update_consumption_logic_app":
                workflow_name = arguments.get("workflow_name")
                result = await self.logicapp_client.update_logic_app(workflow_name, **arguments)
                return self._format_text_response(f"Consumption Logic App '{workflow_name}' updated: {result}")
            
            elif tool_name == "delete_consumption_logic_app":
                workflow_name = arguments.get("workflow_name")
                result = await self.logicapp_client.delete_logic_app(workflow_name)
                return self._format_text_response(f"Consumption Logic App '{workflow_name}' deleted: {result}")
            
            elif tool_name == "enable_consumption_logic_app":
                workflow_name = arguments.get("workflow_name")
                result = await self.logicapp_client.enable_logic_app(workflow_name)
                return self._format_text_response(f"Consumption Logic App '{workflow_name}' enabled: {result}")
            
            elif tool_name == "disable_consumption_logic_app":
                workflow_name = arguments.get("workflow_name")
                result = await self.logicapp_client.disable_logic_app(workflow_name)
                return self._format_text_response(f"Consumption Logic App '{workflow_name}' disabled: {result}")
            
            elif tool_name == "validate_consumption_logic_app":
                result = await self.logicapp_client.validate_logic_app(**arguments)
                return self._format_json_response(result)
            
            elif tool_name == "get_logic_app_callback_url":
                workflow_name = arguments.get("workflow_name")
                trigger_name = arguments.get("trigger_name", "manual")
                result = await self.logicapp_client.get_callback_url(workflow_name, trigger_name)
                return self._format_json_response(result)
            
            elif tool_name == "get_logic_app_swagger":
                workflow_name = arguments.get("workflow_name")
                result = await self.logicapp_client.get_swagger_definition(workflow_name)
                return self._format_json_response(result)
            
            # Workflow Runs Management
            elif tool_name == "list_consumption_workflow_runs":
                workflow_name = arguments.get("workflow_name")
                top = arguments.get("top", 30)
                filter_expr = arguments.get("filter")
                result = await self.logicapp_client.list_workflow_runs(workflow_name, top, filter_expr)
                return self._format_json_response(result)
            
            elif tool_name == "get_consumption_workflow_run":
                workflow_name = arguments.get("workflow_name")
                run_name = arguments.get("run_name")
                result = await self.logicapp_client.get_workflow_run(workflow_name, run_name)
                return self._format_json_response(result)
            
            elif tool_name == "cancel_consumption_workflow_run":
                workflow_name = arguments.get("workflow_name")
                run_name = arguments.get("run_name")
                result = await self.logicapp_client.cancel_workflow_run(workflow_name, run_name)
                return self._format_text_response(f"Workflow run '{run_name}' cancelled: {result}")
            
            elif tool_name == "resubmit_consumption_workflow_run":
                workflow_name = arguments.get("workflow_name")
                run_name = arguments.get("run_name")
                result = await self.logicapp_client.resubmit_workflow_run(workflow_name, run_name)
                return self._format_text_response(f"Workflow run '{run_name}' resubmitted: {result}")
            
            # Workflow Triggers Management
            elif tool_name == "list_consumption_workflow_triggers":
                workflow_name = arguments.get("workflow_name")
                result = await self.logicapp_client.list_workflow_triggers(workflow_name)
                return self._format_json_response(result)
            
            elif tool_name == "get_consumption_workflow_trigger":
                workflow_name = arguments.get("workflow_name")
                trigger_name = arguments.get("trigger_name")
                result = await self.logicapp_client.get_workflow_trigger(workflow_name, trigger_name)
                return self._format_json_response(result)
            
            elif tool_name == "run_consumption_workflow_trigger":
                workflow_name = arguments.get("workflow_name")
                trigger_name = arguments.get("trigger_name")
                result = await self.logicapp_client.run_workflow_trigger(workflow_name, trigger_name)
                return self._format_text_response(f"Trigger '{trigger_name}' executed: {result}")
            
            elif tool_name == "reset_consumption_workflow_trigger":
                workflow_name = arguments.get("workflow_name")
                trigger_name = arguments.get("trigger_name")
                result = await self.logicapp_client.reset_workflow_trigger(workflow_name, trigger_name)
                return self._format_text_response(f"Trigger '{trigger_name}' reset: {result}")
            
            elif tool_name == "get_trigger_schema":
                workflow_name = arguments.get("workflow_name")
                trigger_name = arguments.get("trigger_name")
                result = await self.logicapp_client.get_trigger_schema(workflow_name, trigger_name)
                return self._format_json_response(result)
            
            # Workflow Trigger Histories
            elif tool_name == "list_trigger_histories":
                workflow_name = arguments.get("workflow_name")
                trigger_name = arguments.get("trigger_name")
                top = arguments.get("top", 30)
                result = await self.logicapp_client.list_trigger_histories(workflow_name, trigger_name, top)
                return self._format_json_response(result)
            
            elif tool_name == "get_trigger_history":
                workflow_name = arguments.get("workflow_name")
                trigger_name = arguments.get("trigger_name")
                history_name = arguments.get("history_name")
                result = await self.logicapp_client.get_trigger_history(workflow_name, trigger_name, history_name)
                return self._format_json_response(result)
            
            # Workflow Run Actions
            elif tool_name == "list_workflow_run_actions":
                workflow_name = arguments.get("workflow_name")
                run_name = arguments.get("run_name")
                top = arguments.get("top", 30)
                result = await self.logicapp_client.list_workflow_run_actions(workflow_name, run_name, top)
                return self._format_json_response(result)
            
            elif tool_name == "get_workflow_run_action":
                workflow_name = arguments.get("workflow_name")
                run_name = arguments.get("run_name")
                action_name = arguments.get("action_name")
                result = await self.logicapp_client.get_workflow_run_action(workflow_name, run_name, action_name)
                return self._format_json_response(result)
            
            # Workflow Versions
            elif tool_name == "list_workflow_versions":
                workflow_name = arguments.get("workflow_name")
                top = arguments.get("top", 30)
                result = await self.logicapp_client.list_workflow_versions(workflow_name, top)
                return self._format_json_response(result)
            
            elif tool_name == "get_workflow_version":
                workflow_name = arguments.get("workflow_name")
                version_id = arguments.get("version_id")
                result = await self.logicapp_client.get_workflow_version(workflow_name, version_id)
                return self._format_json_response(result)
            
            # Integration Account Management
            elif tool_name == "list_integration_accounts":
                top = arguments.get("top", 30)
                result = await self.logicapp_client.list_integration_accounts(top)
                return self._format_json_response(result)
            
            elif tool_name == "get_integration_account":
                integration_account_name = arguments.get("integration_account_name")
                result = await self.logicapp_client.get_integration_account(integration_account_name)
                return self._format_json_response(result)
            
            elif tool_name == "create_integration_account":
                integration_account_name = arguments.get("integration_account_name")
                sku = arguments.get("sku", "Free")
                location = arguments.get("location")
                result = await self.logicapp_client.create_integration_account(integration_account_name, sku, location)
                return self._format_text_response(f"Integration account '{integration_account_name}' created: {result}")
            
            elif tool_name == "delete_integration_account":
                integration_account_name = arguments.get("integration_account_name")
                result = await self.logicapp_client.delete_integration_account(integration_account_name)
                return self._format_text_response(f"Integration account '{integration_account_name}' deleted: {result}")
            
            elif tool_name == "list_integration_account_maps":
                integration_account_name = arguments.get("integration_account_name")
                top = arguments.get("top", 30)
                result = await self.logicapp_client.list_integration_account_maps(integration_account_name, top)
                return self._format_json_response(result)
            
            elif tool_name == "list_integration_account_schemas":
                integration_account_name = arguments.get("integration_account_name")
                top = arguments.get("top", 30)
                result = await self.logicapp_client.list_integration_account_schemas(integration_account_name, top)
                return self._format_json_response(result)
            
            elif tool_name == "list_integration_account_partners":
                integration_account_name = arguments.get("integration_account_name")
                top = arguments.get("top", 30)
                result = await self.logicapp_client.list_integration_account_partners(integration_account_name, top)
                return self._format_json_response(result)
            
            elif tool_name == "list_integration_account_agreements":
                integration_account_name = arguments.get("integration_account_name")
                top = arguments.get("top", 30)
                result = await self.logicapp_client.list_integration_account_agreements(integration_account_name, top)
                return self._format_json_response(result)
            
            elif tool_name == "get_integration_account_callback_url":
                integration_account_name = arguments.get("integration_account_name")
                key_type = arguments.get("key_type", "Primary")
                result = await self.logicapp_client.get_integration_account_callback_url(integration_account_name, key_type)
                return self._format_json_response(result)
            
            # Legacy/Compatibility APIs
            elif tool_name == "trigger_consumption_logic_app":
                workflow_name = arguments.get("workflow_name")
                trigger_name = arguments.get("trigger_name", "manual")
                kwargs = {k: v for k, v in arguments.items() if k not in ["workflow_name", "trigger_name"]}
                result = await self.logicapp_client.trigger_logic_app(workflow_name, trigger_name, **kwargs)
                return self._format_json_response(result)
            
            elif tool_name == "get_consumption_run_history":
                workflow_name = arguments.get("workflow_name")
                limit = arguments.get("limit", 10)
                result = await self.logicapp_client.get_run_history(workflow_name, limit)
                return self._format_json_response(result)
            
            elif tool_name == "get_consumption_metrics":
                workflow_name = arguments.get("workflow_name")
                days = arguments.get("days", 7)
                result = await self.logicapp_client.get_consumption_metrics(workflow_name, days)
                return self._format_json_response(result)
            
            elif tool_name == "configure_http_trigger":
                workflow_name = arguments.get("workflow_name")
                trigger_config = arguments.get("trigger_config")
                result = await self.logicapp_client.configure_http_trigger(workflow_name, trigger_config)
                return self._format_text_response(f"HTTP trigger configured for '{workflow_name}': {result}")
            
            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
        
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error executing {tool_name}: {str(e)}"
                }
            }
    
    def _format_json_response(self, data: Any) -> Dict[str, Any]:
        """Format data as JSON response"""
        return {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(data, indent=2, ensure_ascii=False)
                    }
                ]
            }
        }
    
    def _format_text_response(self, text: str) -> Dict[str, Any]:
        """Format text as response"""
        return {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
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