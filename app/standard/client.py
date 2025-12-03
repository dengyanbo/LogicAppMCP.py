"""
Logic App Standard Client

Handles Logic App Standard (dedicated hosting) specific operations.
Standard Logic Apps run on dedicated App Service plans with more control and features.
"""

from typing import Dict, Any, List, Optional
from azure.mgmt.logic.models import Workflow
import logging
from azure.mgmt.web import WebSiteManagementClient
import httpx
import json
import subprocess
import asyncio
import os

from ..shared.base_client import AzureContext, BaseLogicAppClient
from ..config import settings


class StandardLogicAppClient(BaseLogicAppClient):
    """Azure Logic Apps Standard Client"""

    def __init__(self, context: Optional[AzureContext] = None):
        super().__init__(context)
        self.web_client: Optional[WebSiteManagementClient] = None
        self._initialize_web_client()

    def configure_context(self, context: AzureContext):
        """(Re)configure both logic and web clients for a new context."""
        super().configure_context(context)
        self._initialize_web_client()
    
    def _initialize_web_client(self):
        """Initialize Web client for App Service operations"""
        self.web_client = None
        try:
            if self.credential and self.subscription_id:
                self.web_client = WebSiteManagementClient(
                    credential=self.credential,
                    subscription_id=self.subscription_id
                )
        except Exception as e:
            logging.exception("Failed to initialize Web client: %s", e)
    
    async def _run_az_command(self, command_args: List[str]) -> Dict[str, Any]:
        """Execute Azure CLI command and return parsed JSON result"""
        try:
            # Build the full command
            cmd = ["az"] + command_args + ["--output", "json"]
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                if stdout:
                    return {
                        "success": True,
                        "data": json.loads(stdout.decode()),
                        "raw_output": stdout.decode()
                    }
                else:
                    return {"success": True, "data": None, "raw_output": ""}
            else:
                return {
                    "success": False,
                    "error": stderr.decode() if stderr else "Unknown error",
                    "return_code": process.returncode
                }
        except Exception as e:
            logging.exception("Azure CLI execution failed: %s", e)
            return {"success": False, "error": str(e), "return_code": -1}
    
    async def _run_az_command_simple(self, command_args: List[str]) -> bool:
        """Execute Azure CLI command and return simple success/failure"""
        result = await self._run_az_command(command_args)
        return result.get("success", False)
    
    def _get_plan_type(self) -> str:
        """Get the plan type identifier"""
        return "standard"
    
    def _is_compatible_plan_type(self, workflow) -> bool:
        """Check if workflow is Standard plan"""
        # Standard Logic Apps run on App Service plans
        # They have specific characteristics that differentiate them from consumption
        try:
            # Check if it's associated with an App Service plan
            if hasattr(workflow, 'sku') and workflow.sku:
                return workflow.sku.name.lower() in ['ws1', 'ws2', 'ws3']  # Standard SKUs
            
            # Additional checks for standard plan characteristics
            # Standard apps often have more complex configurations
            return False
        except:
            return False
    
    async def create_logic_app(self, workflow_name: str, definition: Dict[str, Any], **kwargs) -> bool:
        """Create new Standard Logic App"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            # Standard-specific workflow configuration
            workflow_params = {
                "location": settings.LOGIC_APP_LOCATION,
                "definition": definition,
            }
            
            # Add Standard-specific parameters
            if "app_service_plan_id" in kwargs:
                workflow_params["sku"] = {
                    "name": kwargs.get("sku_name", "WS1"),
                    "plan": {
                        "id": kwargs["app_service_plan_id"]
                    }
                }
            
            # Add VNET integration if specified
            if "vnet_config" in kwargs:
                workflow_params["vnet_configuration"] = kwargs["vnet_config"]
            
            # Add managed identity configuration
            if "managed_identity" in kwargs:
                workflow_params["identity"] = kwargs["managed_identity"]
            
            workflow = Workflow(**workflow_params)
            
            result = self.client.workflows.create_or_update(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                workflow=workflow
            )
            
            return result is not None
        except Exception as e:
            logging.exception("Error creating Standard Logic App %s: %s", workflow_name, e)
            return False
    
    async def trigger_logic_app(self, workflow_name: str, trigger_name: str = "manual", **kwargs) -> Dict[str, Any]:
        """Trigger Standard Logic App execution"""
        if not self.client or not self.resource_group:
            return {"success": False, "error": "Client not initialized"}
        
        try:
            # Get trigger callback URL
            callback_url = await self._call_sync(
                self.client.workflow_triggers.list_callback_url,
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name,
            )
            
            # Prepare request data for standard
            headers = {"Content-Type": "application/json"}
            data = kwargs.get("payload", {})
            
            # Add authentication headers if needed for Standard
            if "auth_header" in kwargs:
                headers.update(kwargs["auth_header"])
            
            # Send POST request to trigger execution
            async with httpx.AsyncClient(timeout=kwargs.get("timeout", 30)) as client:
                response = await client.post(
                    callback_url.value,
                    json=data,
                    headers=headers,
                )
                return {
                    "success": response.status_code == 202,
                    "status_code": response.status_code,
                    "response": response.text,
                    "plan_type": "standard",
                }
        except Exception as e:
            logging.exception("Error triggering Standard Logic App %s: %s", workflow_name, e)
            return {"success": False, "error": str(e), "plan_type": "standard"}
    
    async def get_app_service_info(self, app_name: str) -> Dict[str, Any]:
        """Get App Service information for Standard Logic App"""
        if not self.web_client or not self.resource_group:
            return {}
        
        try:
            site = await self._call_sync(
                self.web_client.web_apps.get,
                resource_group_name=self.resource_group,
                name=app_name,
            )
            
            return {
                "name": site.name,
                "state": site.state,
                "host_names": site.host_names,
                "repository_site_name": site.repository_site_name,
                "usage_state": site.usage_state,
                "enabled": site.enabled,
                "availability_state": site.availability_state,
                "server_farm_id": site.server_farm_id,
                "last_modified_time": site.last_modified_time.isoformat() if site.last_modified_time else None,
                "plan_type": "standard"
            }
        except Exception as e:
            logging.exception("Error getting App Service info for %s: %s", app_name, e)
            return {}
    
    async def scale_app_service_plan(self, plan_name: str, instance_count: int, sku_name: str = None) -> bool:
        """Scale App Service plan for Standard Logic Apps"""
        if not self.web_client or not self.resource_group:
            return False
        
        try:
            # Get current plan
            plan = await self._call_sync(
                self.web_client.app_service_plans.get,
                resource_group_name=self.resource_group,
                name=plan_name,
            )
            
            # Update scaling settings
            plan.number_of_workers = instance_count
            if sku_name:
                plan.sku.name = sku_name
            
            # Apply changes
            result = await self._call_sync(
                self.web_client.app_service_plans.create_or_update,
                resource_group_name=self.resource_group,
                name=plan_name,
                app_service_plan=plan,
            )
            
            return result is not None
        except Exception as e:
            logging.exception("Error scaling App Service plan %s: %s", plan_name, e)
            return False
    
    async def configure_vnet_integration(self, app_name: str, vnet_config: Dict[str, Any]) -> bool:
        """Configure VNET integration for Standard Logic App"""
        if not self.web_client or not self.resource_group:
            return False
        
        try:
            # Configure VNET integration
            vnet_info = {
                "vnet_resource_id": vnet_config["vnet_resource_id"],
                "subnet_resource_id": vnet_config["subnet_resource_id"],
                "cert_thumbprint": vnet_config.get("cert_thumbprint"),
                "cert_blob": vnet_config.get("cert_blob"),
                "routes": vnet_config.get("routes", [])
            }
            
            result = await self._call_sync(
                self.web_client.web_apps.create_or_update_vnet_connection,
                resource_group_name=self.resource_group,
                name=app_name,
                vnet_name=vnet_config["vnet_name"],
                connection_envelope=vnet_info,
            )
            
            return result is not None
        except Exception as e:
            logging.exception("Error configuring VNET integration for %s: %s", app_name, e)
            return False
    
    async def get_standard_metrics(self, app_name: str, workflow_name: str = None) -> Dict[str, Any]:
        """Get Standard-specific metrics (performance, scaling, etc.)"""
        if not self.web_client or not self.resource_group:
            return {}
        
        try:
            # Get App Service metrics
            metrics = await self._call_sync(
                self.web_client.web_apps.list_metrics,
                resource_group_name=self.resource_group,
                name=app_name,
                details=True,
            )
            
            # Process metrics for Standard Logic Apps
            processed_metrics = {
                "cpu_percentage": [],
                "memory_percentage": [],
                "http_requests": [],
                "response_time": [],
                "plan_type": "standard"
            }
            
            for metric in metrics:
                metric_name = getattr(getattr(metric, "name", None), "value", None) or getattr(metric, "name", None)
                metric_values = getattr(metric, "metric_values", []) or []
                if metric_name == "CpuPercentage":
                    processed_metrics["cpu_percentage"] = [getattr(point, "average", None) for point in metric_values if getattr(point, "average", None) is not None]
                elif metric_name == "MemoryPercentage":
                    processed_metrics["memory_percentage"] = [getattr(point, "average", None) for point in metric_values if getattr(point, "average", None) is not None]
                elif metric_name == "Requests":
                    processed_metrics["http_requests"] = [getattr(point, "total", None) for point in metric_values if getattr(point, "total", None) is not None]
                elif metric_name == "AverageResponseTime":
                    processed_metrics["response_time"] = [getattr(point, "average", None) for point in metric_values if getattr(point, "average", None) is not None]
            
            # Add workflow-specific metrics if specified
            if workflow_name:
                workflow_runs = await self.get_run_history(workflow_name, limit=100)
                processed_metrics["workflow_executions"] = len(workflow_runs)
                processed_metrics["workflow_success_rate"] = len([r for r in workflow_runs if r["status"] == "Succeeded"]) / len(workflow_runs) * 100 if workflow_runs else 0
            
            return processed_metrics
        except Exception as e:
            logging.exception("Error getting Standard metrics for %s: %s", app_name, e)
            return {}
    
    # Azure CLI-based methods for Logic App Standard operations
    
    async def cli_create_logic_app(self, name: str, resource_group: str = None, 
                                  storage_account: str = None, plan: str = None, 
                                  **kwargs) -> Dict[str, Any]:
        """Create Logic App using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "create",
            "--name", name,
            "--resource-group", resource_group
        ]
        
        if storage_account:
            command_args.extend(["--storage-account", storage_account])
        if plan:
            command_args.extend(["--plan", plan])
        if kwargs.get("app_insights"):
            command_args.extend(["--app-insights", kwargs["app_insights"]])
        if kwargs.get("deployment_container_image_name"):
            command_args.extend(["--deployment-container-image-name", kwargs["deployment_container_image_name"]])
        if kwargs.get("https_only"):
            command_args.extend(["--https-only", str(kwargs["https_only"]).lower()])
        if kwargs.get("runtime_version"):
            command_args.extend(["--runtime-version", kwargs["runtime_version"]])
        if kwargs.get("functions_version"):
            command_args.extend(["--functions-version", str(kwargs["functions_version"])])
        if kwargs.get("tags"):
            # Convert tags dict to string format: key=value key2=value2
            if isinstance(kwargs["tags"], dict):
                tag_strings = [f"{k}={v}" for k, v in kwargs["tags"].items()]
                command_args.extend(["--tags"] + tag_strings)
            else:
                command_args.extend(["--tags", kwargs["tags"]])
        
        return await self._run_az_command(command_args)
    
    async def cli_show_logic_app(self, name: str, resource_group: str = None) -> Dict[str, Any]:
        """Get Logic App details using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "show",
            "--name", name,
            "--resource-group", resource_group
        ]
        
        return await self._run_az_command(command_args)
    
    async def cli_list_logic_apps(self, resource_group: str = None) -> Dict[str, Any]:
        """List Logic Apps using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group:
            return {"success": False, "error": "Missing resource group"}
        
        command_args = [
            "logicapp", "list",
            "--resource-group", resource_group
        ]
        
        return await self._run_az_command(command_args)
    
    async def cli_start_logic_app(self, name: str, resource_group: str = None, 
                                 slot: str = None) -> Dict[str, Any]:
        """Start Logic App using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "start",
            "--name", name,
            "--resource-group", resource_group
        ]
        
        if slot:
            command_args.extend(["--slot", slot])
        
        return await self._run_az_command(command_args)
    
    async def cli_stop_logic_app(self, name: str, resource_group: str = None, 
                                slot: str = None) -> Dict[str, Any]:
        """Stop Logic App using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "stop",
            "--name", name,
            "--resource-group", resource_group
        ]
        
        if slot:
            command_args.extend(["--slot", slot])
        
        return await self._run_az_command(command_args)
    
    async def cli_restart_logic_app(self, name: str, resource_group: str = None, 
                                   slot: str = None) -> Dict[str, Any]:
        """Restart Logic App using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "restart",
            "--name", name,
            "--resource-group", resource_group
        ]
        
        if slot:
            command_args.extend(["--slot", slot])
        
        return await self._run_az_command(command_args)
    
    async def cli_scale_logic_app(self, name: str, instance_count: int, 
                                 resource_group: str = None) -> Dict[str, Any]:
        """Scale Logic App using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "scale",
            "--name", name,
            "--resource-group", resource_group,
            "--number-of-workers", str(instance_count)
        ]
        
        return await self._run_az_command(command_args)
    
    async def cli_update_logic_app(self, name: str, resource_group: str = None, 
                                  plan: str = None, slot: str = None, **kwargs) -> Dict[str, Any]:
        """Update Logic App using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "update",
            "--name", name,
            "--resource-group", resource_group
        ]
        
        if plan:
            command_args.extend(["--plan", plan])
        if slot:
            command_args.extend(["--slot", slot])
        
        # Handle generic update arguments
        if kwargs.get("set"):
            if isinstance(kwargs["set"], list):
                for item in kwargs["set"]:
                    command_args.extend(["--set", item])
            else:
                command_args.extend(["--set", kwargs["set"]])
        
        if kwargs.get("add"):
            if isinstance(kwargs["add"], list):
                for item in kwargs["add"]:
                    command_args.extend(["--add", item])
            else:
                command_args.extend(["--add", kwargs["add"]])
        
        if kwargs.get("remove"):
            if isinstance(kwargs["remove"], list):
                for item in kwargs["remove"]:
                    command_args.extend(["--remove", item])
            else:
                command_args.extend(["--remove", kwargs["remove"]])
        
        return await self._run_az_command(command_args)
    
    async def cli_delete_logic_app(self, name: str, resource_group: str = None, 
                                  slot: str = None) -> Dict[str, Any]:
        """Delete Logic App using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "delete",
            "--name", name,
            "--resource-group", resource_group,
            "--yes"  # Skip confirmation
        ]
        
        if slot:
            command_args.extend(["--slot", slot])
        
        return await self._run_az_command(command_args)
    
    async def cli_config_appsettings_list(self, name: str, resource_group: str = None, 
                                         slot: str = None) -> Dict[str, Any]:
        """List Logic App settings using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "config", "appsettings", "list",
            "--name", name,
            "--resource-group", resource_group
        ]
        
        if slot:
            command_args.extend(["--slot", slot])
        
        return await self._run_az_command(command_args)
    
    async def cli_config_appsettings_set(self, name: str, settings: Dict[str, str], 
                                        resource_group: str = None, slot: str = None) -> Dict[str, Any]:
        """Set Logic App settings using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name or not settings:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "config", "appsettings", "set",
            "--name", name,
            "--resource-group", resource_group
        ]
        
        # Add settings in key=value format
        for key, value in settings.items():
            command_args.extend(["--settings", f"{key}={value}"])
        
        if slot:
            command_args.extend(["--slot", slot])
        
        return await self._run_az_command(command_args)
    
    async def cli_config_appsettings_delete(self, name: str, setting_names: List[str], 
                                           resource_group: str = None, slot: str = None) -> Dict[str, Any]:
        """Delete Logic App settings using Azure CLI"""
        resource_group = resource_group or self.resource_group
        if not resource_group or not name or not setting_names:
            return {"success": False, "error": "Missing required parameters"}
        
        command_args = [
            "logicapp", "config", "appsettings", "delete",
            "--name", name,
            "--resource-group", resource_group,
            "--setting-names"
        ] + setting_names
        
        if slot:
            command_args.extend(["--slot", slot])
        
        return await self._run_az_command(command_args)