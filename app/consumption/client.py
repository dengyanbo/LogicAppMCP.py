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
    
    # Additional Workflow Management Methods
    async def update_logic_app(self, workflow_name: str, **kwargs) -> bool:
        """Update an existing Consumption Logic App"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            # Get existing workflow
            existing_workflow = self.client.workflows.get(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name
            )
            
            # Prepare update parameters
            workflow_params = {
                "location": existing_workflow.location,
                "definition": kwargs.get("definition", existing_workflow.definition),
                "parameters": kwargs.get("parameters", existing_workflow.parameters),
                "state": kwargs.get("state", existing_workflow.state)
            }
            
            workflow = Workflow(**workflow_params)
            
            result = self.client.workflows.create_or_update(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                workflow=workflow
            )
            
            return result is not None
        except Exception as e:
            print(f"Error updating Logic App {workflow_name}: {e}")
            return False
    
    async def delete_logic_app(self, workflow_name: str) -> bool:
        """Delete a Consumption Logic App"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            self.client.workflows.delete(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name
            )
            return True
        except Exception as e:
            print(f"Error deleting Logic App {workflow_name}: {e}")
            return False
    
    async def enable_logic_app(self, workflow_name: str) -> bool:
        """Enable a Consumption Logic App"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            self.client.workflows.enable(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name
            )
            return True
        except Exception as e:
            print(f"Error enabling Logic App {workflow_name}: {e}")
            return False
    
    async def disable_logic_app(self, workflow_name: str) -> bool:
        """Disable a Consumption Logic App"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            self.client.workflows.disable(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name
            )
            return True
        except Exception as e:
            print(f"Error disabling Logic App {workflow_name}: {e}")
            return False
    
    async def validate_logic_app(self, **kwargs) -> Dict[str, Any]:
        """Validate a Logic App definition"""
        if not self.client or not self.resource_group:
            return {"error": "Client not initialized"}
        
        try:
            workflow_name = kwargs.get("workflow_name")
            definition = kwargs.get("definition")
            parameters = kwargs.get("parameters", {})
            
            workflow_params = {
                "location": settings.LOGIC_APP_LOCATION,
                "definition": definition,
                "parameters": parameters
            }
            
            workflow = Workflow(**workflow_params)
            
            if workflow_name:
                # Validate existing workflow
                result = self.client.workflows.validate(
                    resource_group_name=self.resource_group,
                    workflow_name=workflow_name,
                    workflow=workflow
                )
            else:
                # Validate new workflow definition
                result = self.client.workflows.validate_workflow(
                    resource_group_name=self.resource_group,
                    location=settings.LOGIC_APP_LOCATION,
                    workflow=workflow
                )
            
            return {"valid": True, "result": result}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def get_callback_url(self, workflow_name: str, trigger_name: str = "manual") -> Dict[str, Any]:
        """Get callback URL for a Logic App trigger"""
        if not self.client or not self.resource_group:
            return {"error": "Client not initialized"}
        
        try:
            callback_url = self.client.workflow_triggers.list_callback_url(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name
            )
            
            return {"callback_url": callback_url.value}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_swagger_definition(self, workflow_name: str) -> Dict[str, Any]:
        """Get OpenAPI/Swagger definition for a Logic App"""
        if not self.client or not self.resource_group:
            return {"error": "Client not initialized"}
        
        try:
            swagger = self.client.workflows.list_swagger(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name
            )
            
            return swagger
        except Exception as e:
            return {"error": str(e)}
    
    # Workflow Runs Management
    async def list_workflow_runs(self, workflow_name: str, top: int = 30, filter_expr: Optional[str] = None) -> List[Dict[str, Any]]:
        """List workflow runs for a Logic App"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            runs = self.client.workflow_runs.list(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                top=top,
                filter=filter_expr
            )
            
            return [self._serialize_workflow_run(run) for run in runs]
        except Exception as e:
            print(f"Error listing workflow runs for {workflow_name}: {e}")
            return []
    
    async def get_workflow_run(self, workflow_name: str, run_name: str) -> Dict[str, Any]:
        """Get details for a specific workflow run"""
        if not self.client or not self.resource_group:
            return {}
        
        try:
            run = self.client.workflow_runs.get(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                run_name=run_name
            )
            
            return self._serialize_workflow_run(run)
        except Exception as e:
            print(f"Error getting workflow run {run_name}: {e}")
            return {}
    
    async def cancel_workflow_run(self, workflow_name: str, run_name: str) -> bool:
        """Cancel a running workflow execution"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            self.client.workflow_runs.cancel(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                run_name=run_name
            )
            return True
        except Exception as e:
            print(f"Error cancelling workflow run {run_name}: {e}")
            return False
    
    async def resubmit_workflow_run(self, workflow_name: str, run_name: str) -> bool:
        """Resubmit a failed workflow run"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            # Get the original run to resubmit
            original_run = self.client.workflow_runs.get(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                run_name=run_name
            )
            
            # Trigger the workflow again with the same inputs
            callback_url = self.client.workflow_triggers.list_callback_url(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name="manual"  # Assuming manual trigger for resubmission
            )
            
            # Send POST request to resubmit
            response = requests.post(
                callback_url.value,
                json=original_run.trigger.inputs if hasattr(original_run.trigger, 'inputs') else {},
                headers={"Content-Type": "application/json"}
            )
            
            return response.status_code == 202
        except Exception as e:
            print(f"Error resubmitting workflow run {run_name}: {e}")
            return False
    
    # Workflow Triggers Management
    async def list_workflow_triggers(self, workflow_name: str) -> List[Dict[str, Any]]:
        """List triggers for a Logic App"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            triggers = self.client.workflow_triggers.list(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name
            )
            
            return [self._serialize_workflow_trigger(trigger) for trigger in triggers]
        except Exception as e:
            print(f"Error listing workflow triggers for {workflow_name}: {e}")
            return []
    
    async def get_workflow_trigger(self, workflow_name: str, trigger_name: str) -> Dict[str, Any]:
        """Get details for a specific workflow trigger"""
        if not self.client or not self.resource_group:
            return {}
        
        try:
            trigger = self.client.workflow_triggers.get(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name
            )
            
            return self._serialize_workflow_trigger(trigger)
        except Exception as e:
            print(f"Error getting workflow trigger {trigger_name}: {e}")
            return {}
    
    async def run_workflow_trigger(self, workflow_name: str, trigger_name: str) -> bool:
        """Manually run a workflow trigger"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            self.client.workflow_triggers.run(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name
            )
            return True
        except Exception as e:
            print(f"Error running workflow trigger {trigger_name}: {e}")
            return False
    
    async def reset_workflow_trigger(self, workflow_name: str, trigger_name: str) -> bool:
        """Reset a workflow trigger state"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            self.client.workflow_triggers.reset(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name
            )
            return True
        except Exception as e:
            print(f"Error resetting workflow trigger {trigger_name}: {e}")
            return False
    
    async def get_trigger_schema(self, workflow_name: str, trigger_name: str) -> Dict[str, Any]:
        """Get JSON schema for a workflow trigger"""
        if not self.client or not self.resource_group:
            return {}
        
        try:
            schema = self.client.workflow_triggers.get_schema_json(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name
            )
            
            return schema
        except Exception as e:
            print(f"Error getting trigger schema for {trigger_name}: {e}")
            return {}
    
    # Workflow Trigger Histories
    async def list_trigger_histories(self, workflow_name: str, trigger_name: str, top: int = 30) -> List[Dict[str, Any]]:
        """List trigger history for a workflow trigger"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            histories = self.client.workflow_trigger_histories.list(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name,
                top=top
            )
            
            return [self._serialize_trigger_history(history) for history in histories]
        except Exception as e:
            print(f"Error listing trigger histories for {trigger_name}: {e}")
            return []
    
    async def get_trigger_history(self, workflow_name: str, trigger_name: str, history_name: str) -> Dict[str, Any]:
        """Get specific trigger history details"""
        if not self.client or not self.resource_group:
            return {}
        
        try:
            history = self.client.workflow_trigger_histories.get(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                trigger_name=trigger_name,
                history_name=history_name
            )
            
            return self._serialize_trigger_history(history)
        except Exception as e:
            print(f"Error getting trigger history {history_name}: {e}")
            return {}
    
    # Workflow Run Actions
    async def list_workflow_run_actions(self, workflow_name: str, run_name: str, top: int = 30) -> List[Dict[str, Any]]:
        """List actions for a specific workflow run"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            actions = self.client.workflow_run_actions.list(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                run_name=run_name,
                top=top
            )
            
            return [self._serialize_workflow_run_action(action) for action in actions]
        except Exception as e:
            print(f"Error listing workflow run actions for {run_name}: {e}")
            return []
    
    async def get_workflow_run_action(self, workflow_name: str, run_name: str, action_name: str) -> Dict[str, Any]:
        """Get details for a specific workflow run action"""
        if not self.client or not self.resource_group:
            return {}
        
        try:
            action = self.client.workflow_run_actions.get(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                run_name=run_name,
                action_name=action_name
            )
            
            return self._serialize_workflow_run_action(action)
        except Exception as e:
            print(f"Error getting workflow run action {action_name}: {e}")
            return {}
    
    # Workflow Versions
    async def list_workflow_versions(self, workflow_name: str, top: int = 30) -> List[Dict[str, Any]]:
        """List all versions of a workflow"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            versions = self.client.workflow_versions.list(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                top=top
            )
            
            return [self._serialize_workflow_version(version) for version in versions]
        except Exception as e:
            print(f"Error listing workflow versions for {workflow_name}: {e}")
            return []
    
    async def get_workflow_version(self, workflow_name: str, version_id: str) -> Dict[str, Any]:
        """Get details for a specific workflow version"""
        if not self.client or not self.resource_group:
            return {}
        
        try:
            version = self.client.workflow_versions.get(
                resource_group_name=self.resource_group,
                workflow_name=workflow_name,
                version_id=version_id
            )
            
            return self._serialize_workflow_version(version)
        except Exception as e:
            print(f"Error getting workflow version {version_id}: {e}")
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
    
    # Helper methods for serialization
    def _serialize_workflow_run(self, run) -> Dict[str, Any]:
        """Serialize workflow run object to dictionary"""
        return {
            "id": run.id,
            "name": run.name,
            "type": run.type,
            "status": run.status,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "correlation_id": run.correlation_id,
            "trigger": {
                "name": run.trigger.name if run.trigger else None,
                "status": run.trigger.status if run.trigger else None,
                "start_time": run.trigger.start_time.isoformat() if run.trigger and run.trigger.start_time else None
            }
        }
    
    def _serialize_workflow_trigger(self, trigger) -> Dict[str, Any]:
        """Serialize workflow trigger object to dictionary"""
        return {
            "id": trigger.id,
            "name": trigger.name,
            "type": trigger.type,
            "provisioning_state": trigger.provisioning_state,
            "created_time": trigger.created_time.isoformat() if trigger.created_time else None,
            "changed_time": trigger.changed_time.isoformat() if trigger.changed_time else None,
            "state": trigger.state
        }
    
    def _serialize_trigger_history(self, history) -> Dict[str, Any]:
        """Serialize trigger history object to dictionary"""
        return {
            "id": history.id,
            "name": history.name,
            "type": history.type,
            "status": history.status,
            "code": history.code,
            "start_time": history.start_time.isoformat() if history.start_time else None,
            "end_time": history.end_time.isoformat() if history.end_time else None,
            "fired": history.fired
        }
    
    def _serialize_workflow_run_action(self, action) -> Dict[str, Any]:
        """Serialize workflow run action object to dictionary"""
        return {
            "id": action.id,
            "name": action.name,
            "type": action.type,
            "status": action.status,
            "code": action.code,
            "start_time": action.start_time.isoformat() if action.start_time else None,
            "end_time": action.end_time.isoformat() if action.end_time else None
        }
    
    def _serialize_workflow_version(self, version) -> Dict[str, Any]:
        """Serialize workflow version object to dictionary"""
        return {
            "id": version.id,
            "name": version.name,
            "type": version.type,
            "version": version.version,
            "created_time": version.created_time.isoformat() if version.created_time else None,
            "changed_time": version.changed_time.isoformat() if version.changed_time else None,
            "state": version.state
        }
    
    # Integration Account Management
    async def list_integration_accounts(self, top: int = 30) -> List[Dict[str, Any]]:
        """List integration accounts in the subscription"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            integration_accounts = self.client.integration_accounts.list_by_resource_group(
                resource_group_name=self.resource_group,
                top=top
            )
            
            return [self._serialize_integration_account(account) for account in integration_accounts]
        except Exception as e:
            print(f"Error listing integration accounts: {e}")
            return []
    
    async def get_integration_account(self, integration_account_name: str) -> Dict[str, Any]:
        """Get details for a specific integration account"""
        if not self.client or not self.resource_group:
            return {}
        
        try:
            account = self.client.integration_accounts.get(
                resource_group_name=self.resource_group,
                integration_account_name=integration_account_name
            )
            
            return self._serialize_integration_account(account)
        except Exception as e:
            print(f"Error getting integration account {integration_account_name}: {e}")
            return {}
    
    async def create_integration_account(self, integration_account_name: str, sku: str = "Free", location: Optional[str] = None) -> bool:
        """Create a new integration account"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            from azure.mgmt.logic.models import IntegrationAccount, IntegrationAccountSku
            
            account_location = location or settings.LOGIC_APP_LOCATION
            
            integration_account = IntegrationAccount(
                location=account_location,
                sku=IntegrationAccountSku(name=sku)
            )
            
            result = self.client.integration_accounts.create_or_update(
                resource_group_name=self.resource_group,
                integration_account_name=integration_account_name,
                integration_account=integration_account
            )
            
            return result is not None
        except Exception as e:
            print(f"Error creating integration account {integration_account_name}: {e}")
            return False
    
    async def delete_integration_account(self, integration_account_name: str) -> bool:
        """Delete an integration account"""
        if not self.client or not self.resource_group:
            return False
        
        try:
            self.client.integration_accounts.delete(
                resource_group_name=self.resource_group,
                integration_account_name=integration_account_name
            )
            return True
        except Exception as e:
            print(f"Error deleting integration account {integration_account_name}: {e}")
            return False
    
    async def list_integration_account_maps(self, integration_account_name: str, top: int = 30) -> List[Dict[str, Any]]:
        """List maps in an integration account"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            maps = self.client.maps.list(
                resource_group_name=self.resource_group,
                integration_account_name=integration_account_name,
                top=top
            )
            
            return [self._serialize_integration_account_map(map_item) for map_item in maps]
        except Exception as e:
            print(f"Error listing maps for {integration_account_name}: {e}")
            return []
    
    async def list_integration_account_schemas(self, integration_account_name: str, top: int = 30) -> List[Dict[str, Any]]:
        """List schemas in an integration account"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            schemas = self.client.schemas.list(
                resource_group_name=self.resource_group,
                integration_account_name=integration_account_name,
                top=top
            )
            
            return [self._serialize_integration_account_schema(schema) for schema in schemas]
        except Exception as e:
            print(f"Error listing schemas for {integration_account_name}: {e}")
            return []
    
    async def list_integration_account_partners(self, integration_account_name: str, top: int = 30) -> List[Dict[str, Any]]:
        """List partners in an integration account"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            partners = self.client.partners.list(
                resource_group_name=self.resource_group,
                integration_account_name=integration_account_name,
                top=top
            )
            
            return [self._serialize_integration_account_partner(partner) for partner in partners]
        except Exception as e:
            print(f"Error listing partners for {integration_account_name}: {e}")
            return []
    
    async def list_integration_account_agreements(self, integration_account_name: str, top: int = 30) -> List[Dict[str, Any]]:
        """List agreements in an integration account"""
        if not self.client or not self.resource_group:
            return []
        
        try:
            agreements = self.client.agreements.list(
                resource_group_name=self.resource_group,
                integration_account_name=integration_account_name,
                top=top
            )
            
            return [self._serialize_integration_account_agreement(agreement) for agreement in agreements]
        except Exception as e:
            print(f"Error listing agreements for {integration_account_name}: {e}")
            return []
    
    async def get_integration_account_callback_url(self, integration_account_name: str, key_type: str = "Primary") -> Dict[str, Any]:
        """Get callback URL for an integration account"""
        if not self.client or not self.resource_group:
            return {"error": "Client not initialized"}
        
        try:
            from azure.mgmt.logic.models import GetCallbackUrlParameters
            from datetime import datetime, timedelta
            
            # Set expiry to 1 hour from now
            not_after = datetime.utcnow() + timedelta(hours=1)
            
            callback_params = GetCallbackUrlParameters(
                key_type=key_type,
                not_after=not_after
            )
            
            callback_url = self.client.integration_accounts.get_callback_url(
                resource_group_name=self.resource_group,
                integration_account_name=integration_account_name,
                get_callback_url_parameters=callback_params
            )
            
            return {"callback_url": callback_url.value}
        except Exception as e:
            return {"error": str(e)}
    
    # Additional serialization helpers for Integration Account objects
    def _serialize_integration_account(self, account) -> Dict[str, Any]:
        """Serialize integration account object to dictionary"""
        return {
            "id": account.id,
            "name": account.name,
            "type": account.type,
            "location": account.location,
            "sku": {
                "name": account.sku.name if account.sku else None
            },
            "properties": account.properties if hasattr(account, 'properties') else {}
        }
    
    def _serialize_integration_account_map(self, map_item) -> Dict[str, Any]:
        """Serialize integration account map object to dictionary"""
        return {
            "id": map_item.id,
            "name": map_item.name,
            "type": map_item.type,
            "map_type": map_item.map_type,
            "created_time": map_item.created_time.isoformat() if map_item.created_time else None,
            "changed_time": map_item.changed_time.isoformat() if map_item.changed_time else None,
            "content_type": map_item.content_type
        }
    
    def _serialize_integration_account_schema(self, schema) -> Dict[str, Any]:
        """Serialize integration account schema object to dictionary"""
        return {
            "id": schema.id,
            "name": schema.name,
            "type": schema.type,
            "schema_type": schema.schema_type,
            "target_namespace": schema.target_namespace,
            "document_name": schema.document_name,
            "created_time": schema.created_time.isoformat() if schema.created_time else None,
            "changed_time": schema.changed_time.isoformat() if schema.changed_time else None,
            "content_type": schema.content_type
        }
    
    def _serialize_integration_account_partner(self, partner) -> Dict[str, Any]:
        """Serialize integration account partner object to dictionary"""
        return {
            "id": partner.id,
            "name": partner.name,
            "type": partner.type,
            "partner_type": partner.partner_type,
            "created_time": partner.created_time.isoformat() if partner.created_time else None,
            "changed_time": partner.changed_time.isoformat() if partner.changed_time else None,
            "metadata": partner.metadata if hasattr(partner, 'metadata') else {}
        }
    
    def _serialize_integration_account_agreement(self, agreement) -> Dict[str, Any]:
        """Serialize integration account agreement object to dictionary"""
        return {
            "id": agreement.id,
            "name": agreement.name,
            "type": agreement.type,
            "agreement_type": agreement.agreement_type,
            "host_partner": agreement.host_partner,
            "guest_partner": agreement.guest_partner,
            "created_time": agreement.created_time.isoformat() if agreement.created_time else None,
            "changed_time": agreement.changed_time.isoformat() if agreement.changed_time else None,
            "metadata": agreement.metadata if hasattr(agreement, 'metadata') else {}
        }