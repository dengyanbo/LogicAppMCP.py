# Logic App MCP Server

A Model Context Protocol (MCP) server for managing Azure Logic Apps through FastAPI.

## Project Structure

```
logicappmcp.py/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration management (Azure credentials, etc.)
│   ├── logicapp_client.py   # Logic App operations wrapper
│   └── mcp_handler.py       # MCP request handling
├── pyproject.toml           # Project configuration and dependencies
├── README.md                # Project documentation
├── .gitignore               # Git ignore file
└── .python-version          # Python version
```

## Features

- 🚀 **FastAPI Web API**: Provides HTTP interface for Logic App management
- 🔧 **MCP Protocol Support**: Implements Model Context Protocol server
- ☁️ **Azure Integration**: Complete Azure Logic Apps management functionality
- 📊 **Runtime Monitoring**: View Logic App execution history and status
- ⚡ **Async Processing**: High-performance asynchronous request handling

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

- `GET /` - Health check
- `GET /health` - Service status
- `GET /logic-apps` - List all Logic Apps
- `POST /mcp/request` - Handle MCP requests

### MCP Tools

The server provides the following MCP tools:

1. **list_logic_apps** - List all Logic Apps
2. **get_logic_app** - Get specific Logic App details
3. **create_logic_app** - Create new Logic App
4. **trigger_logic_app** - Trigger Logic App execution
5. **get_run_history** - Get run history

## Development

### Project Structure Description

- **app/main.py**: FastAPI application main entry point, defines HTTP routes
- **app/config.py**: Configuration management, including Azure credentials and server settings
- **app/logicapp_client.py**: Azure Logic Apps client, wraps all Logic App operations
- **app/mcp_handler.py**: MCP protocol handler, implements tool and resource interfaces

### Adding New Features

1. Add new Azure operations in `logicapp_client.py`
2. Add corresponding MCP tools in `mcp_handler.py`
3. Add HTTP API endpoints in `main.py` (optional)

## License

MIT License
