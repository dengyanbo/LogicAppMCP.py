"""
Logic App Standard Client

Handles Logic App Standard (dedicated hosting) specific operations.
Standard Logic Apps run on dedicated App Service plans with more control and features.
"""

from typing import Dict, Any, List, Optional
from azure.mgmt.logic.models import Workflow
from azure.mgmt.web import WebSiteManagementClient
import requests
import json

from ..shared.base_client import BaseLogicAppClient
from ..config import settings


class StandardLogicAppClient(BaseLogicAppClient):
    """Azure Logic Apps Standard Client"""
    
    def __init__(self):
        super().__init__()
        self.web_client: Optional[WebSiteManagementClient] = None
        self._initialize_web_client()
    
    def _initialize_web_client(self):
        """Initialize Web client for App Service operations"""
        try:
            if self.client and self.client._config.credential:
                self.web_client = WebSiteManagementClient(
                    credential=self.client._config.credential,
                    subscription_id=self.subscription_id
                )
        except Exception as e:
            print(f"Failed to initialize Web client: {e}")
    
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
            print(f"Error creating Standard Logic App {workflow_name}: {e}")
            return False
    
    async def trigger_logic_app(self, workflow_name: str, trigger_name: str = "manual", **kwargs) -> Dict[str, Any]:
        """Trigger Standard Logic App execution"""
        if not self.client or not self.resource_group:
            return {"success": False, "error": "Client not initialized"}
        
        try:
            # Get trigger callback URL
            callback_url = self.client.workflow_triggers.list_callback_url(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name
            )
            
            # Prepare request data for standard
            headers = {"Content-Type": "application/json"}
            data = kwargs.get("payload", {})
            
            # Add authentication headers if needed for Standard
            if "auth_header" in kwargs:
                headers.update(kwargs["auth_header"])
            
            # Send POST request to trigger execution
            response = requests.post(
                callback_url.value, 
                json=data, 
                headers=headers,
                timeout=kwargs.get("timeout", 30)
            )
            
            return {
                "success": response.status_code == 202,
                "status_code": response.status_code,
                "response": response.text,
                "plan_type": "standard"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "plan_type": "standard"}
    
    async def get_app_service_info(self, app_name: str) -> Dict[str, Any]:
        """Get App Service information for Standard Logic App"""
        if not self.web_client or not self.resource_group:
            return {}
        
        try:
            site = self.web_client.web_apps.get(
                resource_group_name=self.resource_group,
                name=app_name
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
            print(f"Error getting App Service info for {app_name}: {e}")
            return {}
    
    async def scale_app_service_plan(self, plan_name: str, instance_count: int, sku_name: str = None) -> bool:
        """Scale App Service plan for Standard Logic Apps"""
        if not self.web_client or not self.resource_group:
            return False
        
        try:
            # Get current plan
            plan = self.web_client.app_service_plans.get(
                resource_group_name=self.resource_group,
                name=plan_name
            )
            
            # Update scaling settings
            plan.number_of_workers = instance_count
            if sku_name:
                plan.sku.name = sku_name
            
            # Apply changes
            result = self.web_client.app_service_plans.create_or_update(
                resource_group_name=self.resource_group,
                name=plan_name,
                app_service_plan=plan
            )
            
            return result is not None
        except Exception as e:
            print(f"Error scaling App Service plan {plan_name}: {e}")
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
            
            result = self.web_client.web_apps.create_or_update_vnet_connection(
                resource_group_name=self.resource_group,
                name=app_name,
                vnet_name=vnet_config["vnet_name"],
                connection_envelope=vnet_info
            )
            
            return result is not None
        except Exception as e:
            print(f"Error configuring VNET integration for {app_name}: {e}")
            return False
    
    async def get_standard_metrics(self, app_name: str, workflow_name: str = None) -> Dict[str, Any]:
        """Get Standard-specific metrics (performance, scaling, etc.)"""
        if not self.web_client or not self.resource_group:
            return {}
        
        try:
            # Get App Service metrics
            metrics = self.web_client.web_apps.list_metrics(
                resource_group_name=self.resource_group,
                name=app_name,
                details=True
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
                if metric.name.value == "CpuPercentage":
                    processed_metrics["cpu_percentage"] = [point.average for point in metric.metric_values if point.average]
                elif metric.name.value == "MemoryPercentage":
                    processed_metrics["memory_percentage"] = [point.average for point in metric.metric_values if point.average]
                elif metric.name.value == "Requests":
                    processed_metrics["http_requests"] = [point.total for point in metric.metric_values if point.total]
                elif metric.name.value == "AverageResponseTime":
                    processed_metrics["response_time"] = [point.average for point in metric.metric_values if point.average]
            
            # Add workflow-specific metrics if specified
            if workflow_name:
                workflow_runs = await self.get_run_history(workflow_name, limit=100)
                processed_metrics["workflow_executions"] = len(workflow_runs)
                processed_metrics["workflow_success_rate"] = len([r for r in workflow_runs if r["status"] == "Succeeded"]) / len(workflow_runs) * 100 if workflow_runs else 0
            
            return processed_metrics
        except Exception as e:
            print(f"Error getting Standard metrics for {app_name}: {e}")
            return {}