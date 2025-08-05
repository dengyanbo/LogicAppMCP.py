"""
Logic App Client

Encapsulates Azure Logic Apps operations, including creation, querying, execution, monitoring, and other functionality
"""

import asyncio
from typing import List, Dict, Any, Optional
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.logic import LogicManagementClient
from azure.mgmt.logic.models import Workflow, WorkflowTrigger
import requests
import json

from .config import settings


class LogicAppClient:
    """Azure Logic Apps Client"""
    
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
        """List all Logic Apps"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            workflows = self.client.workflows.list_by_resource_group(
                resource_group_name=self.resource_group
            )
            
            logic_apps = []
            for workflow in workflows:
                logic_apps.append({
                    "name": workflow.name,
                    "id": workflow.id,
                    "location": workflow.location,
                    "state": workflow.state,
                    "definition": workflow.definition,
                    "created_time": workflow.created_time.isoformat() if workflow.created_time else None,
                    "changed_time": workflow.changed_time.isoformat() if workflow.changed_time else None,
                })
            
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
            
            return {
                "name": workflow.name,
                "id": workflow.id,
                "location": workflow.location,
                "state": workflow.state,
                "definition": workflow.definition,
                "parameters": workflow.parameters,
                "created_time": workflow.created_time.isoformat() if workflow.created_time else None,
                "changed_time": workflow.changed_time.isoformat() if workflow.changed_time else None,
            }
        except Exception as e:
            print(f"Error getting Logic App {workflow_name}: {e}")
            return None
    
    async def create_logic_app(self, workflow_name: str, definition: Dict[str, Any]) -> bool:
        """Create new Logic App"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            workflow = Workflow(
                location=settings.LOGIC_APP_LOCATION,
                definition=definition
            )
            
            result = self.client.workflows.create_or_update(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                workflow=workflow
            )
            
            return result is not None
        except Exception as e:
            print(f"Error creating Logic App {workflow_name}: {e}")
            return False
    
    async def trigger_logic_app(self, workflow_name: str, trigger_name: str = "manual") -> Dict[str, Any]:
        """Trigger Logic App execution"""
        if not self.client or not self.resource_group:
            return {"success": False, "error": "Client not initialized"}
        
        try:
            # Get trigger callback URL
            callback_url = self.client.workflow_triggers.list_callback_url(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name
            )
            
            # Send POST request to trigger execution
            response = requests.post(callback_url.value)
            
            return {
                "success": response.status_code == 202,
                "status_code": response.status_code,
                "response": response.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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