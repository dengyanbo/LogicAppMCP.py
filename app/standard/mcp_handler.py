"""
Standard MCP Handler

Handles MCP requests specific to Logic App Standard (dedicated hosting) plans.
"""

import json
from typing import Dict, Any, List, Optional
from .client import StandardLogicAppClient
from ..config import settings
from ..shared import AzureContext


class StandardMCPHandler:
    """MCP Protocol Request Handler for Logic App Standard"""
    
    def __init__(self):
        self.logicapp_client = StandardLogicAppClient()
        self.server_info = {
            "name": f"{settings.MCP_SERVER_NAME}-standard",
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

    def _extract_azure_context(self, params: Dict[str, Any]) -> AzureContext:
        """Build Azure context from request parameters with settings fallback."""
        base_context = AzureContext.from_settings()
        params = params or {}
        # Accept both "azure_context" (new) and "azure" (docs-compatible) envelopes
        azure_params = {}
        if isinstance(params.get("azure_context"), dict):
            azure_params = params.get("azure_context", {})
        elif isinstance(params.get("azure"), dict):
            azure_params = params.get("azure", {})

        return AzureContext(
            subscription_id=azure_params.get("subscription_id")
            or params.get("subscription_id")
            or base_context.subscription_id,
            resource_group=azure_params.get("resource_group")
            or params.get("resource_group")
            or base_context.resource_group,
            tenant_id=azure_params.get("tenant_id")
            or params.get("tenant_id")
            or base_context.tenant_id,
            client_id=azure_params.get("client_id")
            or params.get("client_id")
            or base_context.client_id,
            client_secret=azure_params.get("client_secret")
            or params.get("client_secret")
            or base_context.client_secret,
        )

    def _strip_azure_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove Azure context keys before forwarding to client methods."""
        if not isinstance(params, dict):
            return {}

        cleaned = dict(params)
        cleaned.pop("azure_context", None)
        cleaned.pop("azure", None)
        for key in ("subscription_id", "resource_group", "tenant_id", "client_id", "client_secret"):
            cleaned.pop(key, None)
        return cleaned

    def _get_client(self, params: Dict[str, Any]) -> StandardLogicAppClient:
        """Get a client configured for the current request context."""
        context = self._extract_azure_context(params)
        if self.logicapp_client:
            self.logicapp_client.configure_context(context)
        else:
            self.logicapp_client = StandardLogicAppClient(context)
        return self.logicapp_client
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
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
        """Return list of available tools for Standard Logic Apps"""
        tools = [
            {
                "name": "list_standard_logic_apps",
                "description": "List all Logic App Standard instances",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_standard_logic_app",
                "description": "Get detailed information for a specific Standard Logic App",
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
                "name": "create_standard_logic_app",
                "description": "Create a new Standard Logic App",
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
                        "app_service_plan_id": {
                            "type": "string",
                            "description": "App Service Plan ID for hosting"
                        },
                        "sku_name": {
                            "type": "string",
                            "description": "SKU name (WS1, WS2, WS3)",
                            "default": "WS1"
                        },
                        "vnet_config": {
                            "type": "object",
                            "description": "VNET configuration (optional)"
                        },
                        "managed_identity": {
                            "type": "object",
                            "description": "Managed identity configuration (optional)"
                        }
                    },
                    "required": ["workflow_name", "definition"]
                }
            },
            {
                "name": "trigger_standard_logic_app",
                "description": "Trigger Standard Logic App execution",
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
                        },
                        "auth_header": {
                            "type": "object",
                            "description": "Authentication headers"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Request timeout in seconds",
                            "default": 30
                        }
                    },
                    "required": ["workflow_name"]
                }
            },
            {
                "name": "get_standard_run_history",
                "description": "Get Standard Logic App run history",
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
                "name": "get_app_service_info",
                "description": "Get App Service information for Standard Logic App",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "App Service name"
                        }
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "scale_app_service_plan",
                "description": "Scale App Service plan for Standard Logic Apps",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "plan_name": {
                            "type": "string",
                            "description": "App Service Plan name"
                        },
                        "instance_count": {
                            "type": "integer",
                            "description": "Number of instances to scale to"
                        },
                        "sku_name": {
                            "type": "string",
                            "description": "SKU name to scale to (optional)"
                        }
                    },
                    "required": ["plan_name", "instance_count"]
                }
            },
            {
                "name": "configure_vnet_integration",
                "description": "Configure VNET integration for Standard Logic App",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "App Service name"
                        },
                        "vnet_config": {
                            "type": "object",
                            "description": "VNET configuration",
                            "properties": {
                                "vnet_name": {"type": "string"},
                                "vnet_resource_id": {"type": "string"},
                                "subnet_resource_id": {"type": "string"},
                                "cert_thumbprint": {"type": "string"},
                                "cert_blob": {"type": "string"},
                                "routes": {"type": "array"}
                            },
                            "required": ["vnet_name", "vnet_resource_id", "subnet_resource_id"]
                        }
                    },
                    "required": ["app_name", "vnet_config"]
                }
            },
            {
                "name": "get_standard_metrics",
                "description": "Get Standard-specific metrics and performance data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "App Service name"
                        },
                        "workflow_name": {
                            "type": "string",
                            "description": "Workflow name (optional)"
                        }
                    },
                    "required": ["app_name"]
                }
            },
            
            # Azure CLI-based tools for Logic App Standard
            {
                "name": "cli_create_standard_logic_app",
                "description": "Create Logic App Standard using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        },
                        "storage_account": {
                            "type": "string",
                            "description": "Storage account for the Logic App"
                        },
                        "plan": {
                            "type": "string",
                            "description": "App Service plan name or resource ID"
                        },
                        "app_insights": {
                            "type": "string",
                            "description": "Application Insights name (optional)"
                        },
                        "deployment_container_image_name": {
                            "type": "string",
                            "description": "Container image name (optional)"
                        },
                        "https_only": {
                            "type": "boolean",
                            "description": "Redirect HTTP to HTTPS (optional)"
                        },
                        "runtime_version": {
                            "type": "string",
                            "description": "Runtime version (~14, ~16, ~18) (optional)"
                        },
                        "functions_version": {
                            "type": "integer",
                            "description": "Functions version (default: 4) (optional)"
                        },
                        "tags": {
                            "type": "object",
                            "description": "Tags for the Logic App (optional)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "cli_show_standard_logic_app",
                "description": "Get Logic App Standard details using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "cli_list_standard_logic_apps",
                "description": "List Logic App Standard instances using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "cli_start_standard_logic_app",
                "description": "Start Logic App Standard using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        },
                        "slot": {
                            "type": "string",
                            "description": "Deployment slot name (optional)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "cli_stop_standard_logic_app",
                "description": "Stop Logic App Standard using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        },
                        "slot": {
                            "type": "string",
                            "description": "Deployment slot name (optional)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "cli_restart_standard_logic_app",
                "description": "Restart Logic App Standard using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        },
                        "slot": {
                            "type": "string",
                            "description": "Deployment slot name (optional)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "cli_scale_standard_logic_app",
                "description": "Scale Logic App Standard using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "instance_count": {
                            "type": "integer",
                            "description": "Number of instances to scale to"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        }
                    },
                    "required": ["name", "instance_count"]
                }
            },
            {
                "name": "cli_update_standard_logic_app",
                "description": "Update Logic App Standard using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        },
                        "plan": {
                            "type": "string",
                            "description": "App Service plan name or resource ID (optional)"
                        },
                        "slot": {
                            "type": "string",
                            "description": "Deployment slot name (optional)"
                        },
                        "set": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Set property values (optional)"
                        },
                        "add": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Add objects to list properties (optional)"
                        },
                        "remove": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Remove property or list elements (optional)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "cli_delete_standard_logic_app",
                "description": "Delete Logic App Standard using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        },
                        "slot": {
                            "type": "string",
                            "description": "Deployment slot name (optional)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "cli_config_appsettings_list",
                "description": "List Logic App Standard settings using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        },
                        "slot": {
                            "type": "string",
                            "description": "Deployment slot name (optional)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "cli_config_appsettings_set",
                "description": "Set Logic App Standard settings using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "settings": {
                            "type": "object",
                            "description": "Settings to set as key-value pairs"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        },
                        "slot": {
                            "type": "string",
                            "description": "Deployment slot name (optional)"
                        }
                    },
                    "required": ["name", "settings"]
                }
            },
            {
                "name": "cli_config_appsettings_delete",
                "description": "Delete Logic App Standard settings using Azure CLI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the Logic App"
                        },
                        "setting_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Names of settings to delete"
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "Resource group name (optional, uses default if not provided)"
                        },
                        "slot": {
                            "type": "string",
                            "description": "Deployment slot name (optional)"
                        }
                    },
                    "required": ["name", "setting_names"]
                }
            }
        ]
        self._tools_cache = tools
        self._required_by_tool = {}
        for tool in tools:
            name = tool.get("name")
            required = tool.get("inputSchema", {}).get("required", []) or []
            if name:
                self._required_by_tool[name] = required
        return {"result": {"tools": tools}}
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls for Standard Logic Apps"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {}) or {}
        client = self._get_client(arguments)
        arguments = self._strip_azure_context(arguments)
        
        # Pre-validate required arguments
        if not self._tools_cache:
            await self._handle_tools_list()
        missing = [k for k in self._required_by_tool.get(tool_name, []) if k not in arguments or arguments.get(k) in (None, "")]
        if missing:
            return {"error": {"code": -32602, "message": f"Missing required parameter(s) for {tool_name}: {', '.join(missing)}"}}

        if tool_name == "list_standard_logic_apps":
            result = await client.list_logic_apps()
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
        
        elif tool_name == "get_standard_logic_app":
            workflow_name = arguments.get("workflow_name")
            result = await client.get_logic_app(workflow_name)
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
        
        elif tool_name == "create_standard_logic_app":
            workflow_name = arguments.get("workflow_name")
            definition = arguments.get("definition")
            kwargs = {k: v for k, v in arguments.items() if k not in ["workflow_name", "definition"]}
            result = await client.create_logic_app(workflow_name, definition, **kwargs)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Standard Logic App '{workflow_name}' created: {result}"
                        }
                    ]
                }
            }
        
        elif tool_name == "trigger_standard_logic_app":
            workflow_name = arguments.get("workflow_name")
            trigger_name = arguments.get("trigger_name", "manual")
            kwargs = {k: v for k, v in arguments.items() if k not in ["workflow_name", "trigger_name"]}
            result = await client.trigger_logic_app(workflow_name, trigger_name, **kwargs)
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
        
        elif tool_name == "get_standard_run_history":
            workflow_name = arguments.get("workflow_name")
            limit = arguments.get("limit", 10)
            result = await client.get_run_history(workflow_name, limit)
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
        
        elif tool_name == "get_app_service_info":
            app_name = arguments.get("app_name")
            result = await client.get_app_service_info(app_name)
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
        
        elif tool_name == "scale_app_service_plan":
            plan_name = arguments.get("plan_name")
            instance_count = arguments.get("instance_count")
            sku_name = arguments.get("sku_name")
            result = await client.scale_app_service_plan(plan_name, instance_count, sku_name)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"App Service Plan '{plan_name}' scaled: {result}"
                        }
                    ]
                }
            }
        
        elif tool_name == "configure_vnet_integration":
            app_name = arguments.get("app_name")
            vnet_config = arguments.get("vnet_config")
            result = await client.configure_vnet_integration(app_name, vnet_config)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"VNET integration configured for '{app_name}': {result}"
                        }
                    ]
                }
            }
        
        elif tool_name == "get_standard_metrics":
            app_name = arguments.get("app_name")
            workflow_name = arguments.get("workflow_name")
            result = await client.get_standard_metrics(app_name, workflow_name)
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
        
        # Azure CLI-based tool handlers
        elif tool_name == "cli_create_standard_logic_app":
            name = arguments.get("name")
            kwargs = {k: v for k, v in arguments.items() if k != "name"}
            result = await client.cli_create_logic_app(name, **kwargs)
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
        
        elif tool_name == "cli_show_standard_logic_app":
            name = arguments.get("name")
            resource_group = arguments.get("resource_group")
            result = await client.cli_show_logic_app(name, resource_group)
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
        
        elif tool_name == "cli_list_standard_logic_apps":
            resource_group = arguments.get("resource_group")
            result = await client.cli_list_logic_apps(resource_group)
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
        
        elif tool_name == "cli_start_standard_logic_app":
            name = arguments.get("name")
            resource_group = arguments.get("resource_group")
            slot = arguments.get("slot")
            result = await client.cli_start_logic_app(name, resource_group, slot)
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
        
        elif tool_name == "cli_stop_standard_logic_app":
            name = arguments.get("name")
            resource_group = arguments.get("resource_group")
            slot = arguments.get("slot")
            result = await client.cli_stop_logic_app(name, resource_group, slot)
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
        
        elif tool_name == "cli_restart_standard_logic_app":
            name = arguments.get("name")
            resource_group = arguments.get("resource_group")
            slot = arguments.get("slot")
            result = await client.cli_restart_logic_app(name, resource_group, slot)
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
        
        elif tool_name == "cli_scale_standard_logic_app":
            name = arguments.get("name")
            instance_count = arguments.get("instance_count")
            resource_group = arguments.get("resource_group")
            result = await client.cli_scale_logic_app(name, instance_count, resource_group)
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
        
        elif tool_name == "cli_update_standard_logic_app":
            name = arguments.get("name")
            kwargs = {k: v for k, v in arguments.items() if k != "name"}
            result = await client.cli_update_logic_app(name, **kwargs)
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
        
        elif tool_name == "cli_delete_standard_logic_app":
            name = arguments.get("name")
            resource_group = arguments.get("resource_group")
            slot = arguments.get("slot")
            result = await client.cli_delete_logic_app(name, resource_group, slot)
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
        
        elif tool_name == "cli_config_appsettings_list":
            name = arguments.get("name")
            resource_group = arguments.get("resource_group")
            slot = arguments.get("slot")
            result = await client.cli_config_appsettings_list(name, resource_group, slot)
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
        
        elif tool_name == "cli_config_appsettings_set":
            name = arguments.get("name")
            settings = arguments.get("settings")
            resource_group = arguments.get("resource_group")
            slot = arguments.get("slot")
            result = await client.cli_config_appsettings_set(name, settings, resource_group, slot)
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
        
        elif tool_name == "cli_config_appsettings_delete":
            name = arguments.get("name")
            setting_names = arguments.get("setting_names")
            resource_group = arguments.get("resource_group")
            slot = arguments.get("slot")
            result = await client.cli_config_appsettings_delete(name, setting_names, resource_group, slot)
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
        """Return list of available resources for Standard Logic Apps"""
        resources = [
            {
                "uri": "logicapp://standard/workflows",
                "name": "Standard Logic Apps List",
                "description": "All Standard Logic Apps in the current subscription",
                "mimeType": "application/json"
            }
        ]
        
        return {"result": {"resources": resources}}
    
    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read resource content for Standard Logic Apps"""
        client = self._get_client(params)
        params = self._strip_azure_context(params)
        uri = params.get("uri")

        if uri == "logicapp://standard/workflows":
            workflows = await client.list_logic_apps()
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