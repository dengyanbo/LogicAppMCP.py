# Logic App MCP Server

A Model Context Protocol (MCP) server for managing Azure Logic Apps through FastAPI.

## Project Structure

```
logicappmcp.py/
├── app/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Configuration management (Azure credentials, etc.)
│   ├── consumption/             # Logic App Consumption (serverless) specific
│   │   ├── __init__.py          # Consumption package initialization
│   │   ├── client.py            # Consumption Logic App client
│   │   └── mcp_handler.py       # Consumption MCP handler
│   ├── standard/                # Logic App Standard (dedicated hosting) specific
│   │   ├── __init__.py          # Standard package initialization
│   │   ├── client.py            # Standard Logic App client
│   │   └── mcp_handler.py       # Standard MCP handler
│   ├── kudu/                    # Kudu services for Standard Logic Apps
│   │   ├── __init__.py          # Kudu package initialization
│   │   ├── client.py            # Kudu REST API client
│   │   └── mcp_handler.py       # Kudu MCP handler
│   └── shared/                  # Shared utilities
│       ├── __init__.py          # Shared package initialization
│       └── base_client.py       # Base client with common functionality
├── pyproject.toml               # Project configuration and dependencies
├── README.md                    # Project documentation
├── .gitignore                   # Git ignore file
└── .python-version              # Python version
```

## Features

- 🚀 **FastAPI Web API**: Provides HTTP interface for Logic App management
- 🔧 **MCP Protocol Support**: Implements Model Context Protocol server for all plan types
- ☁️ **Azure Integration**: Complete Azure Logic Apps management functionality
- 📊 **Runtime Monitoring**: View Logic App execution history and status
- ⚡ **Async Processing**: High-performance asynchronous request handling
- 🏗️ **Plan-Specific Architecture**: Separate clients and handlers for Consumption vs Standard
- 💰 **Consumption Support**: Serverless, pay-per-execution Logic Apps
- 🏢 **Standard Support**: Dedicated hosting with App Service plans and VNET integration
- 🛠️ **Kudu Services**: Complete Kudu REST API access for Standard Logic Apps debugging and file management

## Getting Started for Beginners 🚀

This section provides step-by-step instructions for beginners to get the Logic App MCP Server up and running.

### Prerequisites

Before you begin, make sure you have:

- **Python 3.12 or higher** installed on your system
- **Azure subscription** with Logic Apps service enabled
- **Azure CLI** installed (optional, for Standard Logic Apps)
- **Basic understanding** of Azure Logic Apps concepts

### Step 1: Install Required Tools

#### Install Python
Download and install Python 3.12+ from [python.org](https://python.org)

#### Install uv (Package Manager)
```bash
# Windows (PowerShell)
pip install uv

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Install Azure CLI (Optional)
```bash
# Windows
winget install -e --id Microsoft.AzureCLI

# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### Step 2: Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd logicappmcp.py

# Install project dependencies
uv sync
```

### Step 3: Azure Setup and Authentication

#### Option A: Service Principal (Recommended for Production)

1. **Create Service Principal** in Azure:
   ```bash
   az ad sp create-for-rbac --name "LogicAppMCP" --role contributor
   ```

2. **Note the output** - you'll need:
   - `appId` (Client ID)
   - `password` (Client Secret)
   - `tenant` (Tenant ID)

3. **Get your Subscription ID**:
   ```bash
   az account show --query id --output tsv
   ```

4. **Create Resource Group** (if you don't have one):
   ```bash
   az group create --name "my-logicapp-rg" --location "East US"
   ```

#### Option B: Interactive Login (Good for Development)

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "your-subscription-id"
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Azure Configuration
AZURE_SUBSCRIPTION_ID=your_subscription_id_here
AZURE_RESOURCE_GROUP=your_resource_group_name
AZURE_TENANT_ID=your_tenant_id_here
AZURE_CLIENT_ID=your_client_id_here
AZURE_CLIENT_SECRET=your_client_secret_here

# Server Configuration
HOST=localhost
PORT=8000
DEBUG=true

# Logic App Configuration
LOGIC_APP_LOCATION=East US
```

**⚠️ Security Note**: Never commit your `.env` file to version control. Add it to `.gitignore`.

### Step 5: Start the MCP Server

```bash
# Start the server
uv run python -m app.main
```

You should see output like:
```
INFO:     Uvicorn running on http://localhost:8000
INFO:     Application startup complete.
```

### Step 6: Test the Server

Open a new terminal and test the endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# List Logic Apps (will show empty if none exist)
curl http://localhost:8000/logic-apps
```

### Step 7: Your First MCP Request

Test the MCP server with a simple request to list Logic Apps:

```bash
# Test Consumption Logic Apps MCP endpoint
curl -X POST http://localhost:8000/mcp/consumption/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_consumption_logic_apps",
      "arguments": {}
    }
  }'
```

### Step 8: Create Your First Logic App

Now let's create a simple Logic App to test the full functionality:

```bash
# Create a basic Logic App
curl -X POST http://localhost:8000/mcp/consumption/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "create_consumption_logic_app",
      "arguments": {
        "workflow_name": "my-first-workflow",
        "definition": {
          "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
          "contentVersion": "1.0.0.0",
          "triggers": {
            "manual": {
              "type": "Request",
              "kind": "Http"
            }
          },
          "actions": {
            "hello_world": {
              "type": "Response",
              "inputs": {
                "statusCode": 200,
                "body": {
                  "message": "Hello from Logic App MCP!"
                }
              }
            }
          },
          "outputs": {}
        }
      }
    }
  }'
```

## Common Use Cases and Examples 📚

### 1. List All Your Logic Apps

```bash
# List Consumption Logic Apps
curl -X POST http://localhost:8000/mcp/consumption/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_consumption_logic_apps",
      "arguments": {}
    }
  }'

# List Standard Logic Apps
curl -X POST http://localhost:8000/mcp/standard/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_standard_logic_apps",
      "arguments": {}
    }
  }'

# List files in Standard Logic App via Kudu
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_directory",
      "arguments": {
        "app_name": "my-standard-logicapp",
        "dir_path": "site/wwwroot"
      }
    }
  }'
```

### 2. Get Logic App Details

```bash
# Get specific Logic App information
curl -X POST http://localhost:8000/mcp/consumption/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_consumption_logic_app",
      "arguments": {
        "workflow_name": "my-first-workflow"
      }
    }
  }'
```

### 3. Trigger a Logic App

```bash
# Trigger a Logic App execution
curl -X POST http://localhost:8000/mcp/consumption/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "trigger_consumption_logic_app",
      "arguments": {
        "workflow_name": "my-first-workflow"
      }
    }
  }'
```

### 4. Monitor Logic App Runs

```bash
# Get run history
curl -X POST http://localhost:8000/mcp/consumption/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_consumption_run_history",
      "arguments": {
        "workflow_name": "my-first-workflow"
      }
    }
  }'
```

## Understanding MCP (Model Context Protocol) 🤖

### What is MCP?

The **Model Context Protocol (MCP)** is a standard protocol that allows AI assistants and other tools to communicate with external data sources and services. This Logic App MCP Server implements the MCP specification to provide programmatic access to Azure Logic Apps.

### How MCP Works

1. **MCP Client** (like an AI assistant) sends requests to the MCP Server
2. **MCP Server** (this application) processes requests and calls Azure APIs
3. **Azure Logic Apps** execute workflows and return results
4. **Results** are formatted and sent back to the MCP Client

### MCP Integration Examples

#### With Claude Desktop
```json
{
  "mcpServers": {
    "logicapp": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.main"],
      "env": {
        "AZURE_SUBSCRIPTION_ID": "your-subscription-id",
        "AZURE_RESOURCE_GROUP": "your-resource-group",
        "AZURE_TENANT_ID": "your-tenant-id",
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

#### With Other MCP Clients
Most MCP clients can connect to this server via HTTP endpoints:
- **Consumption Logic Apps**: `http://localhost:8000/mcp/consumption/request`
- **Standard Logic Apps**: `http://localhost:8000/mcp/standard/request`
- **Kudu Services**: `http://localhost:8000/mcp/kudu/request`
- **Generic MCP**: `http://localhost:8000/mcp/request`

## Troubleshooting Guide 🔧

### Common Issues and Solutions

#### 1. Server Won't Start

**Problem**: `ModuleNotFoundError` or import errors
**Solution**: Make sure you're in the project directory and run `uv sync`

**Problem**: Port already in use
**Solution**: Change the port in `.env` file or kill the process using the port

#### 2. Authentication Errors

**Problem**: `Authentication failed` or `Invalid credentials`
**Solution**: 
- Check your `.env` file has correct Azure credentials
- Verify your service principal has proper permissions
- Ensure your subscription is active

#### 3. Logic App Operations Fail

**Problem**: `Resource not found` errors
**Solution**:
- Verify your resource group exists
- Check the Logic App name is correct
- Ensure you're using the right subscription

#### 4. MCP Request Errors

**Problem**: `Method not found` errors
**Solution**:
- Check the tool name spelling
- Verify you're using the correct MCP endpoint (`/mcp/consumption/request` or `/mcp/standard/request`)
- Ensure the request format follows MCP specification

### Debug Mode

Enable debug logging by setting `DEBUG=true` in your `.env` file. This will show detailed error messages and request logs.

### Getting Help

If you encounter issues:

1. **Check the logs** - Look for error messages in the server output
2. **Verify configuration** - Ensure all environment variables are set correctly
3. **Test Azure connectivity** - Try `az account show` to verify Azure CLI authentication
4. **Check permissions** - Ensure your service principal has Logic App Contributor role

## Quick Reference 🚀

### Essential Commands

```bash
# Start server
uv run python -m app.main

# Test health
curl http://localhost:8000/health

# List Logic Apps
curl http://localhost:8000/logic-apps

# MCP request template
curl -X POST http://localhost:8000/mcp/consumption/request \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "tool_name", "arguments": {}}}'
```

### Environment Variables Checklist

- [ ] `AZURE_SUBSCRIPTION_ID` - Your Azure subscription ID
- [ ] `AZURE_RESOURCE_GROUP` - Resource group name
- [ ] `AZURE_TENANT_ID` - Azure tenant ID
- [ ] `AZURE_CLIENT_ID` - Service principal client ID
- [ ] `AZURE_CLIENT_SECRET` - Service principal secret
- [ ] `LOGIC_APP_LOCATION` - Azure region (e.g., "East US")

### Next Steps for Beginners

1. **Complete the setup** - Follow all steps above to get the server running
2. **Create a test Logic App** - Use the example in Step 8 to create your first workflow
3. **Explore the API** - Try different MCP tools to understand the capabilities
4. **Read the detailed documentation** - Check the consumption and standard README files
5. **Build your own workflows** - Create Logic Apps that solve your business problems
6. **Integrate with MCP clients** - Connect AI assistants to manage your Logic Apps

### Learning Resources

- [Azure Logic Apps Documentation](https://docs.microsoft.com/en-us/azure/logic-apps/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/docs)
- [Azure CLI Logic App Commands](https://learn.microsoft.com/en-us/cli/azure/logicapp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Installation and Setup

### 1. Requirements

- Python 3.12+
- uv (package management tool)
- Azure subscription and service principal

### 2. Clone Project

```bash
git clone <repository-url>
cd logicappmcp.py
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Configure Environment Variables

Create `.env` file:

```env
# Azure configuration
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_RESOURCE_GROUP=your_resource_group
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Server configuration
HOST=localhost
PORT=8000
DEBUG=true

# Logic App configuration
LOGIC_APP_LOCATION=East US
```

## Usage

### Start Server

```bash
# Development mode
uv run python -m app.main

# Or
uv run uvicorn app.main:app --reload
```

### API Endpoints

#### General Endpoints
- `GET /` - Health check
- `GET /health` - Service status
- `GET /logic-apps` - List all Logic Apps (both Consumption and Standard)

#### Consumption Logic Apps
- `GET /logic-apps/consumption` - List Consumption Logic Apps only
- `POST /mcp/consumption/request` - Handle MCP requests for Consumption Logic Apps

#### Standard Logic Apps
- `GET /logic-apps/standard` - List Standard Logic Apps only
- `POST /mcp/standard/request` - Handle MCP requests for Standard Logic Apps

#### Kudu Services
- `POST /mcp/kudu/request` - Handle MCP requests for Kudu services (Standard Logic Apps debugging and file management)

#### Legacy Support
- `POST /mcp/request` - Handle generic MCP requests (routes to consumption by default)

### MCP Tools

#### Consumption Logic Apps Tools

1. **list_consumption_logic_apps** - List all Consumption Logic Apps
2. **get_consumption_logic_app** - Get specific Consumption Logic App details
3. **create_consumption_logic_app** - Create new Consumption Logic App
4. **trigger_consumption_logic_app** - Trigger Consumption Logic App execution
5. **get_consumption_run_history** - Get Consumption Logic App run history
6. **get_consumption_metrics** - Get consumption-specific metrics and billing information
7. **configure_http_trigger** - Configure HTTP trigger for Consumption Logic App

#### Standard Logic Apps Tools

1. **list_standard_logic_apps** - List all Standard Logic Apps
2. **get_standard_logic_app** - Get specific Standard Logic App details
3. **create_standard_logic_app** - Create new Standard Logic App
4. **trigger_standard_logic_app** - Trigger Standard Logic App execution
5. **get_standard_run_history** - Get Standard Logic App run history
6. **get_app_service_info** - Get App Service information for Standard Logic App
7. **scale_app_service_plan** - Scale App Service plan for Standard Logic Apps
8. **configure_vnet_integration** - Configure VNET integration for Standard Logic App
9. **get_standard_metrics** - Get Standard-specific metrics and performance data

#### Kudu Services Tools

1. **get_file** - Get file content from Virtual File System
2. **list_directory** - List files and directories
3. **put_file** - Upload file to VFS
4. **create_directory** - Create directory
5. **delete_file** - Delete file from VFS
6. **execute_command** - Execute arbitrary command
7. **list_deployments** - Get deployment history
8. **get_deployment** - Get specific deployment details
9. **redeploy** - Redeploy previous deployment
10. **zip_deploy_from_url** - Deploy from ZIP URL
11. **list_processes** - List running processes
12. **get_process** - Get process details
13. **kill_process** - Kill a process
14. **create_process_dump** - Create process dump for debugging
15. **get_ssh_key** - Get or generate SSH keys
16. **get_environment** - Get environment information
17. **list_webjobs** - List WebJobs
18. **start_webjob** - Start WebJob
19. **stop_webjob** - Stop WebJob
20. **get_scm_info** - Get SCM repository information

*For complete Kudu operations list, see [app/kudu/README.md](app/kudu/README.md)*

## Development

### Project Structure Description

#### Core Components
- **app/main.py**: FastAPI application main entry point, defines HTTP routes for both plan types
- **app/config.py**: Configuration management, including Azure credentials and server settings

#### Consumption Logic Apps (Serverless)
- **app/consumption/client.py**: Consumption Logic App client, handles serverless workflows
- **app/consumption/mcp_handler.py**: MCP protocol handler for Consumption Logic Apps

#### Standard Logic Apps (Dedicated Hosting)
- **app/standard/client.py**: Standard Logic App client, handles App Service-hosted workflows
- **app/standard/mcp_handler.py**: MCP protocol handler for Standard Logic Apps

#### Kudu Services (Standard Logic Apps Management)
- **app/kudu/client.py**: Kudu REST API client, handles file operations, deployments, and debugging
- **app/kudu/mcp_handler.py**: MCP protocol handler for Kudu services

#### Shared Components
- **app/shared/base_client.py**: Base client with common functionality shared between plan types

### Adding New Features

#### For Consumption Logic Apps
1. Add new Azure operations in `app/consumption/client.py`
2. Add corresponding MCP tools in `app/consumption/mcp_handler.py`
3. Add HTTP API endpoints in `main.py` (optional)

#### For Standard Logic Apps
1. Add new Azure operations in `app/standard/client.py`
2. Add corresponding MCP tools in `app/standard/mcp_handler.py`
3. Add HTTP API endpoints in `main.py` (optional)

#### For Kudu Services
1. Add new Kudu operations in `app/kudu/client.py`
2. Add corresponding MCP tools in `app/kudu/mcp_handler.py`
3. Add HTTP API endpoints in `main.py` (optional)

#### For Shared Functionality
1. Add common operations in `app/shared/base_client.py`
2. Inherit and use in consumption, standard, and kudu clients

### Plan Types Comparison

| Feature | Consumption (Serverless) | Standard (Dedicated) |
|---------|-------------------------|---------------------|
| **Hosting** | Azure-managed serverless | App Service plan |
| **Billing** | Pay-per-execution | Always-on pricing |
| **Scaling** | Automatic | Manual/Auto-scale |
| **VNET Integration** | Limited | Full support |
| **Local Development** | Portal/VS Code | Local + Portal |
| **Stateful Workflows** | Limited | Full support |
| **Custom Connectors** | Shared | Isolated |
| **Performance** | Cold start possible | Always warm |

## License

MIT License
