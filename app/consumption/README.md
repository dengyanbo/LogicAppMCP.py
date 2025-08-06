# Logic App Consumption MCP Handler

A comprehensive Model Context Protocol (MCP) handler for Azure Logic Apps Consumption tier, providing full programmatic access to the Microsoft Logic Apps REST API (2016-06-01).

## Overview

This module implements a complete MCP interface for Azure Logic Apps Consumption (serverless) plans, enabling developers to manage workflows, runs, triggers, versions, and integration accounts through the Model Context Protocol.

## Features

- **38 API Operations** across 7 categories
- **Complete Microsoft REST API Coverage** - Aligned with [official documentation](https://learn.microsoft.com/en-us/rest/api/logic/operation-groups?view=rest-logic-2016-06-01)
- **MCP 2024-11-05 Compliant** - Full protocol compliance
- **Async/Await Support** - Non-blocking operations
- **Comprehensive Error Handling** - Robust exception management
- **Azure SDK Integration** - Native Azure SDK support

## Architecture

```
app/consumption/
├── __init__.py           # Package initialization
├── mcp_handler.py        # Main MCP protocol handler
├── client.py            # Azure Logic Apps client implementation
└── README.md           # This documentation
```

## API Operations

### 🔧 Workflow Management (11 operations)

| Operation | Description |
|-----------|-------------|
| `list_consumption_logic_apps` | List all Logic App Consumption instances |
| `get_consumption_logic_app` | Get detailed information for a specific Logic App |
| `create_consumption_logic_app` | Create a new Consumption Logic App |
| `update_consumption_logic_app` | Update an existing Logic App |
| `delete_consumption_logic_app` | Delete a Logic App |
| `enable_consumption_logic_app` | Enable a Logic App |
| `disable_consumption_logic_app` | Disable a Logic App |
| `validate_consumption_logic_app` | Validate a Logic App definition |
| `get_logic_app_callback_url` | Get trigger callback URL |
| `get_logic_app_swagger` | Get OpenAPI/Swagger definition |
| `configure_http_trigger` | Configure HTTP trigger (legacy) |

### 🏃 Workflow Runs (4 operations)

| Operation | Description |
|-----------|-------------|
| `list_consumption_workflow_runs` | List workflow runs with filtering support |
| `get_consumption_workflow_run` | Get specific run details |
| `cancel_consumption_workflow_run` | Cancel a running workflow execution |
| `resubmit_consumption_workflow_run` | Resubmit a failed workflow run |

### ⚡ Workflow Triggers (9 operations)

| Operation | Description |
|-----------|-------------|
| `list_consumption_workflow_triggers` | List all triggers for a workflow |
| `get_consumption_workflow_trigger` | Get details for a specific trigger |
| `run_consumption_workflow_trigger` | Manually run a workflow trigger |
| `reset_consumption_workflow_trigger` | Reset a workflow trigger state |
| `get_trigger_schema` | Get JSON schema for a trigger |
| `list_trigger_histories` | List trigger execution history |
| `get_trigger_history` | Get specific trigger history details |
| `trigger_consumption_logic_app` | Trigger execution (legacy) |
| `get_consumption_run_history` | Get run history (legacy) |

### 🎬 Workflow Run Actions (2 operations)

| Operation | Description |
|-----------|-------------|
| `list_workflow_run_actions` | List actions for a specific workflow run |
| `get_workflow_run_action` | Get details for a specific action |

### 📋 Workflow Versions (2 operations)

| Operation | Description |
|-----------|-------------|
| `list_workflow_versions` | List all versions of a workflow |
| `get_workflow_version` | Get details for a specific version |

### 🔗 Integration Accounts (8 operations)

| Operation | Description |
|-----------|-------------|
| `list_integration_accounts` | List integration accounts |
| `get_integration_account` | Get integration account details |
| `create_integration_account` | Create a new integration account |
| `delete_integration_account` | Delete an integration account |
| `list_integration_account_maps` | List XSLT transformation maps |
| `list_integration_account_schemas` | List XML schemas |
| `list_integration_account_partners` | List B2B trading partners |
| `list_integration_account_agreements` | List B2B agreements |
| `get_integration_account_callback_url` | Get integration account callback URL |

### 📊 Monitoring & Analytics (1 operation)

| Operation | Description |
|-----------|-------------|
| `get_consumption_metrics` | Get consumption-specific metrics and billing |

## Usage Examples

### Basic Workflow Management

```python
from app.consumption.mcp_handler import ConsumptionMCPHandler

# Initialize handler
handler = ConsumptionMCPHandler()

# List all Logic Apps
request = {
    "method": "tools/call",
    "params": {
        "name": "list_consumption_logic_apps",
        "arguments": {}
    }
}
response = await handler.handle_request(request)

# Create a new Logic App
request = {
    "method": "tools/call",
    "params": {
        "name": "create_consumption_logic_app",
        "arguments": {
            "workflow_name": "my-workflow",
            "definition": {
                "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                "contentVersion": "1.0.0.0",
                "triggers": {
                    "manual": {
                        "type": "Request",
                        "kind": "Http"
                    }
                },
                "actions": {},
                "outputs": {}
            }
        }
    }
}
response = await handler.handle_request(request)
```

### Workflow Execution Management

```python
# List workflow runs with filtering
request = {
    "method": "tools/call",
    "params": {
        "name": "list_consumption_workflow_runs",
        "arguments": {
            "workflow_name": "my-workflow",
            "top": 50,
            "filter": "status eq 'Failed'"
        }
    }
}
response = await handler.handle_request(request)

# Cancel a running workflow
request = {
    "method": "tools/call",
    "params": {
        "name": "cancel_consumption_workflow_run",
        "arguments": {
            "workflow_name": "my-workflow",
            "run_name": "08586676746934337772206998657CU22"
        }
    }
}
response = await handler.handle_request(request)
```

### Trigger Management

```python
# Run a trigger manually
request = {
    "method": "tools/call",
    "params": {
        "name": "run_consumption_workflow_trigger",
        "arguments": {
            "workflow_name": "my-workflow",
            "trigger_name": "manual"
        }
    }
}
response = await handler.handle_request(request)

# Get trigger callback URL
request = {
    "method": "tools/call",
    "params": {
        "name": "get_logic_app_callback_url",
        "arguments": {
            "workflow_name": "my-workflow",
            "trigger_name": "manual"
        }
    }
}
response = await handler.handle_request(request)
```

## Configuration

The handler requires the following Azure configuration (set in `app/config.py`):

```python
# Azure subscription settings
AZURE_SUBSCRIPTION_ID = "your-subscription-id"
AZURE_RESOURCE_GROUP = "your-resource-group"
LOGIC_APP_LOCATION = "your-preferred-location"

# Azure authentication
AZURE_CLIENT_ID = "your-client-id"
AZURE_CLIENT_SECRET = "your-client-secret"
AZURE_TENANT_ID = "your-tenant-id"
```

## Error Handling

All operations include comprehensive error handling:

- **Client Initialization Errors**: Graceful handling of authentication failures
- **Azure API Errors**: Proper exception catching and error message formatting
- **Parameter Validation**: Input validation with clear error messages
- **MCP Protocol Errors**: Standard MCP error codes and responses

Example error response:
```json
{
    "error": {
        "code": -32603,
        "message": "Error executing list_consumption_logic_apps: Authentication failed"
    }
}
```

## Response Formats

### JSON Responses
Most operations return structured JSON data:
```json
{
    "result": {
        "content": [
            {
                "type": "text",
                "text": "{\"workflows\": [...], \"total\": 5}"
            }
        ]
    }
}
```

### Text Responses
Operations like create/delete return confirmation messages:
```json
{
    "result": {
        "content": [
            {
                "type": "text",
                "text": "Logic App 'my-workflow' created successfully"
            }
        ]
    }
}
```

## Dependencies

- `azure-mgmt-logic` - Azure Logic Apps management SDK
- `azure-identity` - Azure authentication
- `requests` - HTTP client for direct API calls
- `typing` - Type hints support

## Technical Details

### Class Structure

- **`ConsumptionMCPHandler`** - Main MCP protocol handler
  - Implements MCP 2024-11-05 specification
  - Handles tool listing, calling, and resource management
  - Provides error handling and response formatting

- **`ConsumptionLogicAppClient`** - Azure Logic Apps client
  - Extends `BaseLogicAppClient` for consumption-specific features
  - Implements all 38 API operations
  - Provides object serialization and data transformation

### Serialization Methods

The client includes specialized serialization for Azure SDK objects:
- `_serialize_workflow_run()` - Workflow execution details
- `_serialize_workflow_trigger()` - Trigger configurations
- `_serialize_trigger_history()` - Trigger execution history
- `_serialize_workflow_run_action()` - Action execution details
- `_serialize_workflow_version()` - Workflow version information
- `_serialize_integration_account()` - Integration account details

## Microsoft REST API Alignment

This implementation provides comprehensive coverage of the Logic Apps REST API as documented in:
- [Logic Apps Operation Groups](https://learn.microsoft.com/en-us/rest/api/logic/operation-groups?view=rest-logic-2016-06-01)
- [Workflows API](https://learn.microsoft.com/en-us/rest/api/logic/workflows?view=rest-logic-2016-06-01)
- [Workflow Runs API](https://learn.microsoft.com/en-us/rest/api/logic/workflow-runs)
- [Workflow Triggers API](https://learn.microsoft.com/en-us/rest/api/logic/workflow-triggers)
- [Integration Accounts API](https://learn.microsoft.com/en-us/rest/api/logic/integration-accounts)

All endpoints follow the documented 2016-06-01 API version specifications.

## Contributing

When adding new operations:

1. Add the tool definition to `_handle_tools_list()` in `mcp_handler.py`
2. Implement the handler in `_handle_tools_call()` in `mcp_handler.py`
3. Add the client method in `client.py`
4. Include appropriate serialization if needed
5. Update this README with the new operation

## License

This implementation follows the same license as the parent project.

---

*Last updated: January 2025*
*API Version: 2016-06-01*
*MCP Protocol: 2024-11-05*