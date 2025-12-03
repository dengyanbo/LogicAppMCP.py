"""
Base Logic App Client

Contains shared functionality for both Consumption and Standard Logic Apps.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.logic import LogicManagementClient
from azure.mgmt.logic.models import Workflow
import json

from ..config import settings


@dataclass
class AzureContext:
    """Azure connection context supplied per request."""

    subscription_id: Optional[str] = None
    resource_group: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    @classmethod
    def from_settings(cls, settings_module=settings) -> "AzureContext":
        """Create a context from default settings."""
        return cls(
            subscription_id=settings_module.AZURE_SUBSCRIPTION_ID,
            resource_group=settings_module.AZURE_RESOURCE_GROUP,
            tenant_id=settings_module.AZURE_TENANT_ID,
            client_id=settings_module.AZURE_CLIENT_ID,
            client_secret=settings_module.AZURE_CLIENT_SECRET,
        )

    def create_credential(self) -> DefaultAzureCredential | ClientSecretCredential:
        """Build a credential, favoring client secret when provided."""
        if self.tenant_id and self.client_id and self.client_secret:
            return ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

        # Fall back to DefaultAzureCredential which expects an active az login session
        return DefaultAzureCredential()


class BaseLogicAppClient:
    """Base Azure Logic Apps Client with shared functionality"""

    def __init__(self, context: Optional[AzureContext] = None):
        self.context = context or AzureContext.from_settings()
        self.subscription_id: Optional[str] = None
        self.resource_group: Optional[str] = None
        self.client: Optional[LogicManagementClient] = None
        self.credential: Optional[DefaultAzureCredential | ClientSecretCredential] = None
        self.configure_context(self.context)

    def configure_context(self, context: AzureContext):
        """(Re)configure the client to use the provided Azure context."""
        self.context = context
        self.subscription_id = context.subscription_id
        self.resource_group = context.resource_group
        self.client = None
        self.credential = None

        try:
            self.credential = context.create_credential()

            if self.subscription_id:
                self.client = LogicManagementClient(
                    credential=self.credential,
                    subscription_id=self.subscription_id
                )
        except Exception as e:
            logging.exception("Failed to initialize Azure client: %s", e)
    
    async def _call_sync(self, func, *args, **kwargs):
        """Run a synchronous SDK call in a thread to avoid blocking the event loop."""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def _list_sync(self, func, *args, **kwargs):
        """Run a synchronous list call and materialize results as a list in a thread."""
        return await asyncio.to_thread(lambda: list(func(*args, **kwargs)))
    
    async def list_logic_apps(self) -> List[Dict[str, Any]]:
        """List all Logic Apps (base implementation)"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            workflows = await self._list_sync(
                self.client.workflows.list_by_resource_group,
                resource_group_name=self.resource_group,
            )
            
            logic_apps = []
            for workflow in workflows:
                logic_app_data = self._format_workflow_data(workflow)
                # Filter by plan type if implemented in subclass
                if self._is_compatible_plan_type(workflow):
                    logic_apps.append(logic_app_data)
            
            return logic_apps
        except Exception as e:
            logging.exception("Error listing Logic Apps: %s", e)
            return []
    
    async def get_logic_app(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get specific Logic App details"""
        if not self.client or not self.resource_group:
            return None
        
        try:
            workflow = await self._call_sync(
                self.client.workflows.get,
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
            )
            
            if not self._is_compatible_plan_type(workflow):
                return None
            
            return self._format_workflow_data(workflow, include_details=True)
        except Exception as e:
            logging.exception("Error getting Logic App %s: %s", workflow_name, e)
            return None
    
    async def get_run_history(self, workflow_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get Logic App run history"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            runs = await self._list_sync(
                self.client.workflow_runs.list,
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                top=limit,
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
            logging.exception("Error getting run history for %s: %s", workflow_name, e)
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