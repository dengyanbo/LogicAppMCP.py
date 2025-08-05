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
- 🔧 **MCP Protocol Support**: Implements Model Context Protocol server for both plan types
- ☁️ **Azure Integration**: Complete Azure Logic Apps management functionality
- 📊 **Runtime Monitoring**: View Logic App execution history and status
- ⚡ **Async Processing**: High-performance asynchronous request handling
- 🏗️ **Plan-Specific Architecture**: Separate clients and handlers for Consumption vs Standard
- 💰 **Consumption Support**: Serverless, pay-per-execution Logic Apps
- 🏢 **Standard Support**: Dedicated hosting with App Service plans and VNET integration

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

#### For Shared Functionality
1. Add common operations in `app/shared/base_client.py`
2. Inherit and use in both consumption and standard clients

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
