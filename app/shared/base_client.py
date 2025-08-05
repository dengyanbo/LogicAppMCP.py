"""
Base Logic App Client

Contains shared functionality for both Consumption and Standard Logic Apps.
"""

import asyncio
from typing import List, Dict, Any, Optional
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.logic import LogicManagementClient
from azure.mgmt.logic.models import Workflow, WorkflowTrigger
import requests
import json

from ..config import settings


class BaseLogicAppClient:
    """Base Azure Logic Apps Client with shared functionality"""
    
    def __init__(self):
        self.subscription_id = settings.AZURE_SUBSCRIPTION_ID
        self.resource_group = settings.AZURE_RESOURCE_GROUP
        self.client: Optional[LogicManagementClient] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure client"""
        try:
            if settings.validate_azure_config():
                # Use service principal authentication
                credential = ClientSecretCredential(
                    tenant_id=settings.AZURE_TENANT_ID,
                    client_id=settings.AZURE_CLIENT_ID,
                    client_secret=settings.AZURE_CLIENT_SECRET
                )
            else:
                # Use default credentials (suitable for local development)
                credential = DefaultAzureCredential()
            
            if self.subscription_id:
                self.client = LogicManagementClient(
                    credential=credential,
                    subscription_id=self.subscription_id
                )
        except Exception as e:
            print(f"Failed to initialize Azure client: {e}")
    
    async def list_logic_apps(self) -> List[Dict[str, Any]]:
        """List all Logic Apps (base implementation)"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            workflows = self.client.workflows.list_by_resource_group(
                resource_group_name=self.resource_group
            )
            
            logic_apps = []
            for workflow in workflows:
                logic_app_data = self._format_workflow_data(workflow)
                # Filter by plan type if implemented in subclass
                if self._is_compatible_plan_type(workflow):
                    logic_apps.append(logic_app_data)
            
            return logic_apps
        except Exception as e:
            print(f"Error listing Logic Apps: {e}")
            return []
    
    async def get_logic_app(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get specific Logic App details"""
        if not self.client or not self.resource_group:
            return None
        
        try:
            workflow = self.client.workflows.get(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name
            )
            
            if not self._is_compatible_plan_type(workflow):
                return None
            
            return self._format_workflow_data(workflow, include_details=True)
        except Exception as e:
            print(f"Error getting Logic App {workflow_name}: {e}")
            return None
    
    async def get_run_history(self, workflow_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get Logic App run history"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            runs = self.client.workflow_runs.list(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                top=limit
            )
            
            run_history = []
            for run in runs:
                run_history.append({
                    "name": run.name,
                    "status": run.status,
                    "start_time": run.start_time.isoformat() if run.start_time else None,
                    "end_time": run.end_time.isoformat() if run.end_time else None,
                    "trigger": run.trigger,
                    "outputs": run.outputs
                })
            
            return run_history
        except Exception as e:
            print(f"Error getting run history for {workflow_name}: {e}")
            return []
    
    def _format_workflow_data(self, workflow, include_details: bool = False) -> Dict[str, Any]:
        """Format workflow data for consistent output"""
        data = {
            "name": workflow.name,
            "id": workflow.id,
            "location": workflow.location,
            "state": workflow.state,
            "created_time": workflow.created_time.isoformat() if workflow.created_time else None,
            "changed_time": workflow.changed_time.isoformat() if workflow.changed_time else None,
            "plan_type": self._get_plan_type(),
        }
        
        if include_details:
            data.update({
                "definition": workflow.definition,
                "parameters": workflow.parameters,
            })
        
        return data
    
    def _is_compatible_plan_type(self, workflow) -> bool:
        """Check if workflow is compatible with this client type"""
        # Base implementation accepts all - override in subclasses
        return True
    
    def _get_plan_type(self) -> str:
        """Get the plan type identifier"""
        # Override in subclasses
        return "unknown"
    
    # Abstract methods to be implemented by subclasses
    async def create_logic_app(self, workflow_name: str, definition: Dict[str, Any], **kwargs) -> bool:
        """Create new Logic App - implement in subclasses"""
        raise NotImplementedError("Subclasses must implement create_logic_app")
    
    async def trigger_logic_app(self, workflow_name: str, trigger_name: str = "manual", **kwargs) -> Dict[str, Any]:
        """Trigger Logic App execution - implement in subclasses"""
        raise NotImplementedError("Subclasses must implement trigger_logic_app")