"""
Kudu MCP Handler

Model Context Protocol handler for Azure Kudu services, providing comprehensive
access to Logic App Standard management, debugging, and file operations.

Implements MCP 2024-11-05 specification with 30+ Kudu operations.
"""

import json
import base64
from typing import Any, Dict, List, Optional

from .client import KuduClient


class KuduMCPHandler:
    """
    MCP Handler for Azure Kudu Services
    
    Provides Model Context Protocol interface for comprehensive Logic App Standard
    management through Azure Kudu REST API operations.
    """

    def __init__(self, azure_context: Optional[Dict[str, Any]] = None):
        """Initialize Kudu MCP handler"""
        self.client = KuduClient(azure_context=azure_context)

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request and route to appropriate method"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            azure_context = request.get("azure_context") or params.get("azure_context")

            if method == "tools/list":
                return await self._handle_tools_list()
            elif method == "tools/call":
                return await self._handle_tools_call(params, azure_context)
            elif method == "resources/list":
                return await self._handle_resources_list()
            elif method == "resources/read":
                return await self._handle_resources_read(params)
            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Method {method} not found"
                    }
                }

        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def _handle_tools_list(self) -> Dict[str, Any]:
        """Return list of available Kudu tools"""
        tools = [
            # SCM Operations
            {
                "name": "get_scm_info",
                "description": "Get SCM repository information for Logic App Standard",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "clean_repository",
                "description": "Clean repository using 'git clean -xdff'",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "delete_repository",
                "description": "Delete the repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"}
                    },
                    "required": ["app_name"]
                }
            },

            # Command Execution
            {
                "name": "execute_command",
                "description": "Execute arbitrary command and return output",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "command": {"type": "string", "description": "Command to execute"},
                        "directory": {"type": "string", "description": "Working directory", "default": "site\\wwwroot"}
                    },
                    "required": ["app_name", "command"]
                }
            },

            # VFS File Operations
            {
                "name": "get_file",
                "description": "Get file content from Virtual File System",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "file_path": {"type": "string", "description": "Path to file"}
                    },
                    "required": ["app_name", "file_path"]
                }
            },
            {
                "name": "list_directory",
                "description": "List files and directories in path",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "dir_path": {"type": "string", "description": "Directory path to list"}
                    },
                    "required": ["app_name", "dir_path"]
                }
            },
            {
                "name": "put_file",
                "description": "Upload file to Virtual File System",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "file_path": {"type": "string", "description": "Target file path"},
                        "content": {"type": "string", "description": "File content"},
                        "encoding": {"type": "string", "description": "Content encoding (text/base64)", "default": "text"}
                    },
                    "required": ["app_name", "file_path", "content"]
                }
            },
            {
                "name": "create_directory",
                "description": "Create directory in Virtual File System",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "dir_path": {"type": "string", "description": "Directory path to create"}
                    },
                    "required": ["app_name", "dir_path"]
                }
            },
            {
                "name": "delete_file",
                "description": "Delete file from Virtual File System",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "file_path": {"type": "string", "description": "File path to delete"}
                    },
                    "required": ["app_name", "file_path"]
                }
            },

            # Zip Operations
            {
                "name": "download_directory_zip",
                "description": "Download directory as zip file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "dir_path": {"type": "string", "description": "Directory path to zip"}
                    },
                    "required": ["app_name", "dir_path"]
                }
            },
            {
                "name": "upload_zip_directory",
                "description": "Upload and extract zip file to directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "dir_path": {"type": "string", "description": "Target directory path"},
                        "zip_content": {"type": "string", "description": "Base64 encoded zip file content"}
                    },
                    "required": ["app_name", "dir_path", "zip_content"]
                }
            },

            # Deployment Operations
            {
                "name": "list_deployments",
                "description": "Get list of all deployments",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "get_deployment",
                "description": "Get specific deployment details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "deployment_id": {"type": "string", "description": "Deployment ID"}
                    },
                    "required": ["app_name", "deployment_id"]
                }
            },
            {
                "name": "redeploy",
                "description": "Redeploy a current or previous deployment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "deployment_id": {"type": "string", "description": "Deployment ID (optional for current)"},
                        "clean": {"type": "boolean", "description": "Run git clean before building", "default": False},
                        "need_file_update": {"type": "boolean", "description": "Run git checkout", "default": True}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "delete_deployment",
                "description": "Delete a deployment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "deployment_id": {"type": "string", "description": "Deployment ID"}
                    },
                    "required": ["app_name", "deployment_id"]
                }
            },
            {
                "name": "get_deployment_log",
                "description": "Get deployment log entries",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "deployment_id": {"type": "string", "description": "Deployment ID"}
                    },
                    "required": ["app_name", "deployment_id"]
                }
            },
            {
                "name": "get_deployment_log_details",
                "description": "Get specific deployment log entry details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "deployment_id": {"type": "string", "description": "Deployment ID"},
                        "log_id": {"type": "string", "description": "Log entry ID"}
                    },
                    "required": ["app_name", "deployment_id", "log_id"]
                }
            },

            # Zip Deployment
            {
                "name": "zip_deploy_from_url",
                "description": "Deploy from zip URL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "package_uri": {"type": "string", "description": "URL to zip package"},
                        "is_async": {"type": "boolean", "description": "Deploy asynchronously", "default": True}
                    },
                    "required": ["app_name", "package_uri"]
                }
            },
            {
                "name": "zip_deploy_from_file",
                "description": "Deploy from zip file content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "zip_content": {"type": "string", "description": "Base64 encoded zip file content"}
                    },
                    "required": ["app_name", "zip_content"]
                }
            },

            # SSH Key Operations
            {
                "name": "get_ssh_key",
                "description": "Get or generate SSH keys",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "ensure_public_key": {"type": "boolean", "description": "Generate public key if missing", "default": True}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "set_private_key",
                "description": "Set private SSH key",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "private_key": {"type": "string", "description": "Private SSH key content"}
                    },
                    "required": ["app_name", "private_key"]
                }
            },
            {
                "name": "delete_ssh_key",
                "description": "Delete SSH key",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"}
                    },
                    "required": ["app_name"]
                }
            },

            # Environment Operations
            {
                "name": "get_environment",
                "description": "Get environment information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "get_settings",
                "description": "Get application settings",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"}
                    },
                    "required": ["app_name"]
                }
            },

            # Process Operations
            {
                "name": "list_processes",
                "description": "List running processes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "get_process",
                "description": "Get specific process details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "process_id": {"type": "string", "description": "Process ID"}
                    },
                    "required": ["app_name", "process_id"]
                }
            },
            {
                "name": "kill_process",
                "description": "Kill a process",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "process_id": {"type": "string", "description": "Process ID"}
                    },
                    "required": ["app_name", "process_id"]
                }
            },
            {
                "name": "create_process_dump",
                "description": "Create process dump for debugging",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "process_id": {"type": "string", "description": "Process ID"},
                        "dump_type": {"type": "string", "description": "Dump type (mini/full)", "default": "mini"}
                    },
                    "required": ["app_name", "process_id"]
                }
            },

            # WebJobs Operations
            {
                "name": "list_webjobs",
                "description": "List WebJobs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "get_webjob",
                "description": "Get WebJob details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "job_name": {"type": "string", "description": "WebJob name"}
                    },
                    "required": ["app_name", "job_name"]
                }
            },
            {
                "name": "start_webjob",
                "description": "Start a WebJob",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "job_name": {"type": "string", "description": "WebJob name"}
                    },
                    "required": ["app_name", "job_name"]
                }
            },
            {
                "name": "stop_webjob",
                "description": "Stop a WebJob",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "Logic App Standard name"},
                        "job_name": {"type": "string", "description": "WebJob name"}
                    },
                    "required": ["app_name", "job_name"]
                }
            }
        ]

        azure_context_schema = {
            "type": "object",
            "description": "Azure context including subscription, resource group, and optional service principal credentials",
            "properties": {
                "subscription_id": {"type": "string"},
                "resource_group": {"type": "string"},
                "tenant_id": {"type": "string"},
                "client_id": {"type": "string"},
                "client_secret": {"type": "string"},
            },
        }

        for tool in tools:
            tool["inputSchema"]["properties"]["azure_context"] = azure_context_schema

        return {"result": {"tools": tools}}

    async def _handle_tools_call(self, params: Dict[str, Any], azure_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle tool call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        merged_context = azure_context or arguments.get("azure_context") or self.client.azure_context

        try:
            # SCM Operations
            if tool_name == "get_scm_info":
                result = await self.client.get_scm_info(arguments["app_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            elif tool_name == "clean_repository":
                result = await self.client.clean_repository(arguments["app_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            elif tool_name == "delete_repository":
                result = await self.client.delete_repository(arguments["app_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            # Command Execution
            elif tool_name == "execute_command":
                result = await self.client.execute_command(
                    arguments["app_name"],
                    arguments["command"],
                    arguments.get("directory", "site\\wwwroot"),
                    azure_context=merged_context,
                )
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            # VFS File Operations
            elif tool_name == "get_file":
                content = await self.client.get_file(arguments["app_name"], arguments["file_path"], azure_context=merged_context)
                try:
                    # Try to decode as text
                    text_content = content.decode('utf-8')
                    return {"result": {"content": [{"type": "text", "text": text_content}]}}
                except UnicodeDecodeError:
                    # Return as base64 for binary files
                    b64_content = base64.b64encode(content).decode('ascii')
                    return {"result": {"content": [{"type": "text", "text": f"Binary file (base64): {b64_content}"}]}}

            elif tool_name == "list_directory":
                result = await self.client.list_directory(arguments["app_name"], arguments["dir_path"], azure_context=merged_context)
                files_info = [self.client._serialize_file_info(f) for f in result]
                return {"result": {"content": [{"type": "text", "text": json.dumps(files_info, indent=2)}]}}

            elif tool_name == "put_file":
                content = arguments["content"]
                encoding = arguments.get("encoding", "text")
                
                if encoding == "base64":
                    content = base64.b64decode(content)
                
                result = await self.client.put_file(arguments["app_name"], arguments["file_path"], content, azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            elif tool_name == "create_directory":
                result = await self.client.create_directory(arguments["app_name"], arguments["dir_path"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            elif tool_name == "delete_file":
                result = await self.client.delete_file(arguments["app_name"], arguments["file_path"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            # Zip Operations
            elif tool_name == "download_directory_zip":
                zip_content = await self.client.download_directory_as_zip(arguments["app_name"], arguments["dir_path"], azure_context=merged_context)
                b64_content = base64.b64encode(zip_content).decode('ascii')
                return {"result": {"content": [{"type": "text", "text": f"Zip file (base64): {b64_content}"}]}}

            elif tool_name == "upload_zip_directory":
                zip_content = base64.b64decode(arguments["zip_content"])
                result = await self.client.upload_zip_to_directory(arguments["app_name"], arguments["dir_path"], zip_content, azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            # Deployment Operations
            elif tool_name == "list_deployments":
                result = await self.client.list_deployments(arguments["app_name"], azure_context=merged_context)
                deployments = [self.client._serialize_deployment_info(d) for d in result]
                return {"result": {"content": [{"type": "text", "text": json.dumps(deployments, indent=2)}]}}

            elif tool_name == "get_deployment":
                result = await self.client.get_deployment(arguments["app_name"], arguments["deployment_id"], azure_context=merged_context)
                deployment = self.client._serialize_deployment_info(result)
                return {"result": {"content": [{"type": "text", "text": json.dumps(deployment, indent=2)}]}}

            elif tool_name == "redeploy":
                result = await self.client.redeploy(
                    arguments["app_name"],
                    arguments.get("deployment_id"),
                    arguments.get("clean", False),
                    arguments.get("need_file_update", True),
                    azure_context=merged_context,
                )
                return {"result": {"content": [{"type": "text", "text": result}]}}

            elif tool_name == "delete_deployment":
                result = await self.client.delete_deployment(arguments["app_name"], arguments["deployment_id"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            elif tool_name == "get_deployment_log":
                result = await self.client.get_deployment_log(arguments["app_name"], arguments["deployment_id"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            elif tool_name == "get_deployment_log_details":
                result = await self.client.get_deployment_log_details(
                    arguments["app_name"],
                    arguments["deployment_id"],
                    arguments["log_id"],
                    azure_context=merged_context,
                )
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            # Zip Deployment
            elif tool_name == "zip_deploy_from_url":
                result = await self.client.zip_deploy_from_url(
                    arguments["app_name"],
                    arguments["package_uri"],
                    arguments.get("is_async", True),
                    azure_context=merged_context,
                )
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            elif tool_name == "zip_deploy_from_file":
                zip_content = base64.b64decode(arguments["zip_content"])
                result = await self.client.zip_deploy_from_file(arguments["app_name"], zip_content, azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            # SSH Key Operations
            elif tool_name == "get_ssh_key":
                result = await self.client.get_ssh_key(
                    arguments["app_name"],
                    arguments.get("ensure_public_key", True),
                    azure_context=merged_context,
                )
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            elif tool_name == "set_private_key":
                result = await self.client.set_private_key(arguments["app_name"], arguments["private_key"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            elif tool_name == "delete_ssh_key":
                result = await self.client.delete_ssh_key(arguments["app_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            # Environment Operations
            elif tool_name == "get_environment":
                result = await self.client.get_environment(arguments["app_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            elif tool_name == "get_settings":
                result = await self.client.get_settings(arguments["app_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            # Process Operations
            elif tool_name == "list_processes":
                result = await self.client.list_processes(arguments["app_name"], azure_context=merged_context)
                processes = [self.client._serialize_process_info(p) for p in result]
                return {"result": {"content": [{"type": "text", "text": json.dumps(processes, indent=2)}]}}

            elif tool_name == "get_process":
                result = await self.client.get_process(arguments["app_name"], arguments["process_id"], azure_context=merged_context)
                process = self.client._serialize_process_info(result)
                return {"result": {"content": [{"type": "text", "text": json.dumps(process, indent=2)}]}}

            elif tool_name == "kill_process":
                result = await self.client.kill_process(arguments["app_name"], arguments["process_id"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            elif tool_name == "create_process_dump":
                dump_content = await self.client.create_process_dump(
                    arguments["app_name"],
                    arguments["process_id"],
                    arguments.get("dump_type", "mini"),
                    azure_context=merged_context,
                )
                b64_content = base64.b64encode(dump_content).decode('ascii')
                return {"result": {"content": [{"type": "text", "text": f"Process dump (base64): {b64_content}"}]}}

            # WebJobs Operations
            elif tool_name == "list_webjobs":
                result = await self.client.list_webjobs(arguments["app_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            elif tool_name == "get_webjob":
                result = await self.client.get_webjob(arguments["app_name"], arguments["job_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}

            elif tool_name == "start_webjob":
                result = await self.client.start_webjob(arguments["app_name"], arguments["job_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            elif tool_name == "stop_webjob":
                result = await self.client.stop_webjob(arguments["app_name"], arguments["job_name"], azure_context=merged_context)
                return {"result": {"content": [{"type": "text", "text": result}]}}

            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Tool {tool_name} not found"
                    }
                }

        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error executing {tool_name}: {str(e)}"
                }
            }

    async def _handle_resources_list(self) -> Dict[str, Any]:
        """Return list of available resources"""
        resources = [
            {
                "uri": "kudu://scm/info",
                "mimeType": "application/json",
                "name": "SCM Information",
                "description": "Repository and SCM information"
            },
            {
                "uri": "kudu://vfs/",
                "mimeType": "application/json",
                "name": "Virtual File System",
                "description": "File system browser and operations"
            },
            {
                "uri": "kudu://deployments/",
                "mimeType": "application/json",
                "name": "Deployments",
                "description": "Deployment history and management"
            },
            {
                "uri": "kudu://processes/",
                "mimeType": "application/json",
                "name": "Processes",
                "description": "Running processes information"
            },
            {
                "uri": "kudu://webjobs/",
                "mimeType": "application/json",
                "name": "WebJobs",
                "description": "WebJobs management"
            }
        ]

        return {"result": {"resources": resources}}

    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource read request"""
        uri = params.get("uri", "")
        
        if uri.startswith("kudu://"):
            resource_type = uri.replace("kudu://", "").split("/")[0]
            
            if resource_type == "scm":
                return {"result": {"contents": [{"type": "text", "text": "SCM resource - use get_scm_info tool"}]}}
            elif resource_type == "vfs":
                return {"result": {"contents": [{"type": "text", "text": "VFS resource - use list_directory tool"}]}}
            elif resource_type == "deployments":
                return {"result": {"contents": [{"type": "text", "text": "Deployments resource - use list_deployments tool"}]}}
            elif resource_type == "processes":
                return {"result": {"contents": [{"type": "text", "text": "Processes resource - use list_processes tool"}]}}
            elif resource_type == "webjobs":
                return {"result": {"contents": [{"type": "text", "text": "WebJobs resource - use list_webjobs tool"}]}}
        
        return {
            "error": {
                "code": -32602,
                "message": f"Resource {uri} not found"
            }
        }
