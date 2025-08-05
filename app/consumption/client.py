"""
Logic App Consumption Client

Handles Logic App Consumption (serverless) specific operations.
Consumption Logic Apps are serverless, pay-per-execution, and Azure-managed.
"""

from typing import Dict, Any, List, Optional
from azure.mgmt.logic.models import Workflow
import requests

from ..shared.base_client import BaseLogicAppClient
from ..config import settings


class ConsumptionLogicAppClient(BaseLogicAppClient):
    """Azure Logic Apps Consumption Client"""
    
    def _get_plan_type(self) -> str:
        """Get the plan type identifier"""
        return "consumption"
    
    def _is_compatible_plan_type(self, workflow) -> bool:
        """Check if workflow is Consumption plan"""
        # Consumption Logic Apps don't have a hosting plan property
        # They are identified by the absence of integration service environment
        # and specific workflow properties
        if hasattr(workflow, 'integration_service_environment') and workflow.integration_service_environment:
            return False
        
        # Additional checks for consumption plan characteristics
        return True
    
    async def create_logic_app(self, workflow_name: str, definition: Dict[str, Any], **kwargs) -> bool:
        """Create new Consumption Logic App"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            # Consumption-specific workflow configuration
            workflow_params = {
                "location": settings.LOGIC_APP_LOCATION,
                "definition": definition,
            }
            
            # Add consumption-specific parameters
            if "parameters" in kwargs:
                workflow_params["parameters"] = kwargs["parameters"]
            
            # Add access control for consumption
            if "access_control" in kwargs:
                workflow_params["access_control"] = kwargs["access_control"]
            
            workflow = Workflow(**workflow_params)
            
            result = self.client.workflows.create_or_update(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                workflow=workflow
            )
            
            return result is not None
        except Exception as e:
            print(f"Error creating Consumption Logic App {workflow_name}: {e}")
            return False
    
    async def trigger_logic_app(self, workflow_name: str, trigger_name: str = "manual", **kwargs) -> Dict[str, Any]:
        """Trigger Consumption Logic App execution"""
        if not self.client or not self.resource_group:
            return {"success": False, "error": "Client not initialized"}
        
        try:
            # Get trigger callback URL
            callback_url = self.client.workflow_triggers.list_callback_url(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name
            )
            
            # Prepare request data for consumption
            headers = {"Content-Type": "application/json"}
            data = kwargs.get("payload", {})
            
            # Send POST request to trigger execution
            response = requests.post(
                callback_url.value, 
                json=data, 
                headers=headers
            )
            
            return {
                "success": response.status_code == 202,
                "status_code": response.status_code,
                "response": response.text,
                "plan_type": "consumption"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "plan_type": "consumption"}
    
    async def get_consumption_metrics(self, workflow_name: str, days: int = 7) -> Dict[str, Any]:
        """Get consumption-specific metrics (billing, executions, etc.)"""
        if not self.client or not self.resource_group:
            return {}
        
        try:
            # Get workflow runs for billing analysis
            runs = self.client.workflow_runs.list(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                top=1000  # Get more runs for analysis
            )
            
            # Calculate consumption metrics
            total_runs = 0
            successful_runs = 0
            failed_runs = 0
            
            for run in runs:
                total_runs += 1
                if run.status == "Succeeded":
                    successful_runs += 1
                elif run.status == "Failed":
                    failed_runs += 1
            
            return {
                "total_executions": total_runs,
                "successful_executions": successful_runs,
                "failed_executions": failed_runs,
                "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
                "estimated_cost_units": total_runs,  # Each execution = 1 unit in consumption
                "plan_type": "consumption"
            }
        except Exception as e:
            print(f"Error getting consumption metrics for {workflow_name}: {e}")
            return {}
    
    async def configure_http_trigger(self, workflow_name: str, trigger_config: Dict[str, Any]) -> bool:
        """Configure HTTP trigger for consumption Logic App"""
        try:
            workflow = self.client.workflows.get(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name
            )
            
            # Update definition with HTTP trigger configuration
            definition = workflow.definition
            if "triggers" not in definition:
                definition["triggers"] = {}
            
            # Configure consumption-specific HTTP trigger
            definition["triggers"]["manual"] = {
                "type": "Request",
                "kind": "Http",
                "inputs": {
                    "schema": trigger_config.get("schema", {}),
                    "method": trigger_config.get("method", ["GET", "POST"]),
                    "relativePath": trigger_config.get("relative_path")
                }
            }
            
            # Update workflow
            updated_workflow = Workflow(
                location=workflow.location,
                definition=definition,
                parameters=workflow.parameters
            )
            
            result = self.client.workflows.create_or_update(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                workflow=updated_workflow
            )
            
            return result is not None
        except Exception as e:
            print(f"Error configuring HTTP trigger for {workflow_name}: {e}")
            return False