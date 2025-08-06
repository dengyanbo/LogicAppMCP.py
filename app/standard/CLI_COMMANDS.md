# Logic App Standard Azure CLI Commands

This document describes the Azure CLI-based functionality implemented for Logic App Standard operations.

## Overview

The Logic App Standard client now includes comprehensive Azure CLI support, enabling you to perform all major Logic App Standard operations using the familiar `az logicapp` commands through the MCP interface.

## Available CLI Methods

### 1. Logic App Lifecycle Management

#### Create Logic App
- **Method**: `cli_create_logic_app`
- **Azure CLI**: `az logicapp create`
- **Description**: Create a new Logic App Standard instance
- **Parameters**:
  - `name` (required): Logic App name
  - `resource_group` (optional): Resource group name
  - `storage_account` (optional): Storage account name
  - `plan` (optional): App Service plan name or resource ID
  - `app_insights` (optional): Application Insights name
  - `deployment_container_image_name` (optional): Container image
  - `https_only` (optional): Force HTTPS redirect
  - `runtime_version` (optional): Runtime version (~14, ~16, ~18)
  - `functions_version` (optional): Functions version (default: 4)
  - `tags` (optional): Resource tags

#### Show Logic App
- **Method**: `cli_show_logic_app`
- **Azure CLI**: `az logicapp show`
- **Description**: Get detailed information about a Logic App
- **Parameters**:
  - `name` (required): Logic App name
  - `resource_group` (optional): Resource group name

#### List Logic Apps
- **Method**: `cli_list_logic_apps`
- **Azure CLI**: `az logicapp list`
- **Description**: List all Logic Apps in a resource group
- **Parameters**:
  - `resource_group` (optional): Resource group name

#### Delete Logic App
- **Method**: `cli_delete_logic_app`
- **Azure CLI**: `az logicapp delete`
- **Description**: Delete a Logic App
- **Parameters**:
  - `name` (required): Logic App name
  - `resource_group` (optional): Resource group name
  - `slot` (optional): Deployment slot name

### 2. Logic App State Management

#### Start Logic App
- **Method**: `cli_start_logic_app`
- **Azure CLI**: `az logicapp start`
- **Description**: Start a stopped Logic App
- **Parameters**:
  - `name` (required): Logic App name
  - `resource_group` (optional): Resource group name
  - `slot` (optional): Deployment slot name

#### Stop Logic App
- **Method**: `cli_stop_logic_app`
- **Azure CLI**: `az logicapp stop`
- **Description**: Stop a running Logic App
- **Parameters**:
  - `name` (required): Logic App name
  - `resource_group` (optional): Resource group name
  - `slot` (optional): Deployment slot name

#### Restart Logic App
- **Method**: `cli_restart_logic_app`
- **Azure CLI**: `az logicapp restart`
- **Description**: Restart a Logic App
- **Parameters**:
  - `name` (required): Logic App name
  - `resource_group` (optional): Resource group name
  - `slot` (optional): Deployment slot name

### 3. Scaling and Updates

#### Scale Logic App
- **Method**: `cli_scale_logic_app`
- **Azure CLI**: `az logicapp scale`
- **Description**: Scale the number of instances
- **Parameters**:
  - `name` (required): Logic App name
  - `instance_count` (required): Number of instances
  - `resource_group` (optional): Resource group name

#### Update Logic App
- **Method**: `cli_update_logic_app`
- **Azure CLI**: `az logicapp update`
- **Description**: Update Logic App configuration
- **Parameters**:
  - `name` (required): Logic App name
  - `resource_group` (optional): Resource group name
  - `plan` (optional): New App Service plan
  - `slot` (optional): Deployment slot name
  - `set` (optional): Array of property updates
  - `add` (optional): Array of property additions
  - `remove` (optional): Array of property removals

### 4. Application Settings Management

#### List App Settings
- **Method**: `cli_config_appsettings_list`
- **Azure CLI**: `az logicapp config appsettings list`
- **Description**: List all application settings
- **Parameters**:
  - `name` (required): Logic App name
  - `resource_group` (optional): Resource group name
  - `slot` (optional): Deployment slot name

#### Set App Settings
- **Method**: `cli_config_appsettings_set`
- **Azure CLI**: `az logicapp config appsettings set`
- **Description**: Set application settings
- **Parameters**:
  - `name` (required): Logic App name
  - `settings` (required): Object with key-value pairs
  - `resource_group` (optional): Resource group name
  - `slot` (optional): Deployment slot name

#### Delete App Settings
- **Method**: `cli_config_appsettings_delete`
- **Azure CLI**: `az logicapp config appsettings delete`
- **Description**: Delete application settings
- **Parameters**:
  - `name` (required): Logic App name
  - `setting_names` (required): Array of setting names to delete
  - `resource_group` (optional): Resource group name
  - `slot` (optional): Deployment slot name

## MCP Tool Names

When using these methods through the MCP interface, use these tool names:

1. `cli_create_standard_logic_app`
2. `cli_show_standard_logic_app`
3. `cli_list_standard_logic_apps`
4. `cli_start_standard_logic_app`
5. `cli_stop_standard_logic_app`
6. `cli_restart_standard_logic_app`
7. `cli_scale_standard_logic_app`
8. `cli_update_standard_logic_app`
9. `cli_delete_standard_logic_app`
10. `cli_config_appsettings_list`
11. `cli_config_appsettings_set`
12. `cli_config_appsettings_delete`

## Usage Examples

### MCP Request Example

```json
{
  "method": "tools/call",
  "params": {
    "name": "cli_create_standard_logic_app",
    "arguments": {
      "name": "my-standard-logicapp",
      "storage_account": "mystorageaccount",
      "plan": "my-app-service-plan",
      "https_only": true,
      "tags": {
        "Environment": "Production",
        "Owner": "DevTeam"
      }
    }
  }
}
```

### Python Client Example

```python
from app.standard.client import StandardLogicAppClient

client = StandardLogicAppClient()

# Create a new Logic App
result = await client.cli_create_logic_app(
    name="my-logicapp",
    storage_account="mystorageaccount",
    plan="my-plan",
    https_only=True
)

# Start the Logic App
result = await client.cli_start_logic_app("my-logicapp")

# Set application settings
result = await client.cli_config_appsettings_set(
    name="my-logicapp",
    settings={
        "MY_SETTING": "value1",
        "ANOTHER_SETTING": "value2"
    }
)
```

## Error Handling

All CLI methods return a standardized response format:

```json
{
  "success": true/false,
  "data": {...},  // CLI command output (if successful)
  "error": "...", // Error message (if failed)
  "return_code": 0, // Process return code
  "raw_output": "..." // Raw CLI output
}
```

## Prerequisites

1. Azure CLI must be installed and available in the system PATH
2. User must be authenticated with Azure CLI (`az login`)
3. Appropriate permissions to manage Logic Apps in the target subscription/resource group

## Notes

- All methods automatically add `--output json` to CLI commands for structured responses
- Resource group parameter is optional and defaults to the configured resource group
- CLI commands are executed asynchronously using Python's `asyncio.create_subprocess_exec`
- Error handling includes both CLI errors and JSON parsing errors
- All CLI operations include proper timeout handling

## Related Documentation

- [Azure CLI Logic App Commands](https://learn.microsoft.com/en-us/cli/azure/logicapp?view=azure-cli-latest)
- [Logic App Standard Documentation](https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-overview)
- [MCP Protocol Specification](https://modelcontextprotocol.io/docs)