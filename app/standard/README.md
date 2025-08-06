# Logic App Standard MCP Handler

A comprehensive Model Context Protocol (MCP) implementation for Azure Logic Apps Standard tier, providing both Azure SDK and Azure CLI-based operations through a unified interface.

## Overview

Logic App Standard runs on dedicated App Service plans, offering more control, features, and enterprise capabilities compared to the Consumption tier. This package provides complete programmatic access to Logic App Standard operations through the MCP protocol.

## Features

### 🔄 **Dual Operation Modes**
- **Azure SDK Integration**: Native Azure management operations
- **Azure CLI Support**: Full CLI command coverage for operations not available in SDK

### 🛠️ **Core Capabilities**
- Logic App lifecycle management (create, read, update, delete)
- App Service plan scaling and management
- VNET integration configuration
- Application settings management
- Run history and monitoring
- Metrics and performance data
- Deployment slot operations

### 📊 **Azure CLI Operations**
- Complete coverage of `az logicapp` commands
- Async CLI execution with proper error handling
- JSON output parsing and standardization
- Resource group and subscription management

## Architecture

```
app/standard/
├── __init__.py           # Package exports
├── client.py             # StandardLogicAppClient implementation
├── mcp_handler.py        # MCP protocol handler
├── CLI_COMMANDS.md       # Azure CLI documentation
└── README.md            # This file
```

## Quick Start

### 1. Initialize the Handler

```python
from app.standard import StandardMCPHandler

handler = StandardMCPHandler()
```

### 2. Handle MCP Requests

```python
# Example MCP request
request = {
    "method": "tools/call",
    "params": {
        "name": "cli_create_standard_logic_app",
        "arguments": {
            "name": "my-logicapp",
            "storage_account": "mystorageaccount",
            "plan": "my-app-service-plan"
        }
    }
}

response = await handler.handle_request(request)
```

## Available Tools

### 📱 **Standard SDK Tools**
| Tool Name | Description |
|-----------|-------------|
| `list_standard_logic_apps` | List all Logic App Standard instances |
| `get_standard_logic_app` | Get detailed Logic App information |
| `create_standard_logic_app` | Create new Logic App with SDK |
| `trigger_standard_logic_app` | Trigger Logic App execution |
| `get_standard_run_history` | Get workflow run history |
| `get_app_service_info` | Get App Service hosting information |
| `scale_app_service_plan` | Scale the App Service plan |
| `configure_vnet_integration` | Configure VNET connectivity |
| `get_standard_metrics` | Get performance metrics |

### 🖥️ **Azure CLI Tools**
| Tool Name | Azure CLI Command | Description |
|-----------|-------------------|-------------|
| `cli_create_standard_logic_app` | `az logicapp create` | Create Logic App via CLI |
| `cli_show_standard_logic_app` | `az logicapp show` | Get Logic App details |
| `cli_list_standard_logic_apps` | `az logicapp list` | List Logic Apps |
| `cli_start_standard_logic_app` | `az logicapp start` | Start Logic App |
| `cli_stop_standard_logic_app` | `az logicapp stop` | Stop Logic App |
| `cli_restart_standard_logic_app` | `az logicapp restart` | Restart Logic App |
| `cli_scale_standard_logic_app` | `az logicapp scale` | Scale Logic App instances |
| `cli_update_standard_logic_app` | `az logicapp update` | Update Logic App configuration |
| `cli_delete_standard_logic_app` | `az logicapp delete` | Delete Logic App |
| `cli_config_appsettings_list` | `az logicapp config appsettings list` | List app settings |
| `cli_config_appsettings_set` | `az logicapp config appsettings set` | Set app settings |
| `cli_config_appsettings_delete` | `az logicapp config appsettings delete` | Delete app settings |

## Usage Examples

### Creating a Logic App with Azure CLI

```json
{
  "method": "tools/call",
  "params": {
    "name": "cli_create_standard_logic_app",
    "arguments": {
      "name": "my-production-logicapp",
      "storage_account": "prodstorageaccount",
      "plan": "/subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Web/serverFarms/my-plan",
      "https_only": true,
      "runtime_version": "~18",
      "tags": {
        "Environment": "Production",
        "Team": "Integration",
        "CostCenter": "IT-001"
      }
    }
  }
}
```

### Managing Application Settings

```json
{
  "method": "tools/call",
  "params": {
    "name": "cli_config_appsettings_set",
    "arguments": {
      "name": "my-logicapp",
      "settings": {
        "STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;...",
        "API_BASE_URL": "https://api.example.com",
        "ENVIRONMENT": "production"
      }
    }
  }
}
```

### Scaling Operations

```json
{
  "method": "tools/call",
  "params": {
    "name": "cli_scale_standard_logic_app",
    "arguments": {
      "name": "my-logicapp",
      "instance_count": 3
    }
  }
}
```

### Getting Performance Metrics

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_standard_metrics",
    "arguments": {
      "app_name": "my-logicapp",
      "workflow_name": "my-workflow"
    }
  }
}
```

## Configuration

### Environment Variables

The client uses these configuration settings from `app/config.py`:

```python
# Azure Authentication
AZURE_SUBSCRIPTION_ID = "your-subscription-id"
AZURE_RESOURCE_GROUP = "your-resource-group"
AZURE_TENANT_ID = "your-tenant-id"
AZURE_CLIENT_ID = "your-client-id"
AZURE_CLIENT_SECRET = "your-client-secret"

# Logic App Settings
LOGIC_APP_LOCATION = "eastus"
```

### Prerequisites

1. **Azure CLI** (for CLI-based operations)
   ```bash
   # Install Azure CLI
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Login to Azure
   az login
   ```

2. **Azure SDK** (for SDK-based operations)
   ```bash
   # Install via uv (recommended)
   uv add azure-mgmt-logic azure-mgmt-web azure-identity
   ```

3. **Permissions**
   - Logic App Contributor role or higher
   - App Service Contributor role (for scaling operations)
   - Storage Account access (for Logic App storage)

## Error Handling

All operations return standardized error responses:

```json
{
  "error": {
    "code": -32603,
    "message": "Specific error description"
  }
}
```

### Common Error Codes
- `-32601`: Method not found
- `-32602`: Invalid parameters
- `-32603`: Internal error (Azure API/CLI failures)

## Best Practices

### 🔒 **Security**
- Never hardcode credentials in workflow definitions
- Use managed identities when possible
- Implement least-privilege access principles
- Regularly rotate secrets and connection strings

### ⚡ **Performance**
- Monitor CPU and memory usage through metrics
- Scale instances based on workload patterns
- Use appropriate App Service plan tiers (WS1, WS2, WS3)
- Implement proper error handling and retry logic

### 🏗️ **Architecture**
- Separate environments (dev/staging/prod) with different resource groups
- Use VNET integration for secure connectivity
- Implement proper logging and monitoring
- Use deployment slots for blue-green deployments

## Integration with Other Services

### App Service Plans
Logic App Standard requires an App Service plan. Recommended configurations:

- **Development**: WS1 (1 vCPU, 3.5 GB RAM)
- **Production**: WS2 or WS3 for better performance
- **High Availability**: Multiple instances across availability zones

### Storage Accounts
Each Logic App Standard requires a dedicated storage account for:
- Workflow state management
- Execution history
- Temporary file storage

### Application Insights
Enable Application Insights for:
- Performance monitoring
- Error tracking
- Custom telemetry
- Dependency tracking

## Troubleshooting

### Common Issues

1. **CLI Command Failures**
   - Ensure Azure CLI is installed and authenticated
   - Verify subscription and resource group access
   - Check CLI version compatibility

2. **SDK Authentication Errors**
   - Verify Azure credentials configuration
   - Check service principal permissions
   - Ensure subscription ID is correct

3. **Logic App Creation Failures**
   - Verify storage account exists and is accessible
   - Check App Service plan capacity
   - Ensure unique Logic App names

### Debug Mode

Enable debug logging by setting the appropriate log level in your application.

## Related Documentation

- [Azure CLI Logic App Commands](https://learn.microsoft.com/en-us/cli/azure/logicapp?view=azure-cli-latest)
- [Logic App Standard Documentation](https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-overview)
- [App Service Plans](https://docs.microsoft.com/en-us/azure/app-service/overview-hosting-plans)
- [MCP Protocol Specification](https://modelcontextprotocol.io/docs)
- [CLI_COMMANDS.md](./CLI_COMMANDS.md) - Detailed CLI command reference

## License

This project follows the same license as the parent LogicAppMCP project.

## Contributing

When contributing to the Standard Logic App implementation:

1. Follow the workspace rules in `.cursor/rules/logicappmcp-rules.mdc`
2. Use type hints and async/await patterns
3. Include proper error handling and documentation
4. Test both SDK and CLI operations
5. Maintain MCP protocol compliance

---

**Note**: This implementation provides comprehensive Logic App Standard management capabilities through both Azure SDK and CLI interfaces, offering flexibility and complete feature coverage for enterprise Logic App deployments.