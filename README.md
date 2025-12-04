# Logic App MCP Server

FastAPI-based Model Context Protocol (MCP) server that lets MCP clients manage Azure Logic Apps (Consumption and Standard) and Kudu via a consistent HTTP surface.

## Quickstart (one screen)
```bash
git clone <repository-url>
cd logicappmcp.py
uv sync

# authenticate locally (used when no client_secret is supplied)
az login

uv run python -m app.main &

# include Azure context in each MCP request
curl http://localhost:8000/health            # health
curl -H "Content-Type: application/json" \
  -d '{"method":"tools/call","params":{"name":"list_consumption_logic_apps","arguments":{"azure":{"subscription_id":"<sub>","resource_group":"<rg>","tenant_id":"<tenant>","client_id":"<app-id>"}}}}' \
  http://localhost:8000/mcp/consumption/request
```

## Architecture at a glance
- **app/main.py**: FastAPI entrypoint exposing `/`, `/health`, and MCP POST routes (`/mcp`, `/mcp/consumption`, `/mcp/standard`, `/mcp/kudu`).
- **MCP handlers**: Each plan has its own `mcp_handler.py` (`app/consumption`, `app/standard`, `app/kudu`) that receives the FastAPI requests and dispatches MCP tool calls.
- **Clients**: Per-plan `client.py` instances talk to Azure APIs (Consumption and Standard ARM/management) or the Kudu REST API (Standard file/process operations).
- **Shared utilities**: `app/shared/base_client.py` provides common auth, request plumbing, and logging used by all clients.

### Module map
```
HTTP/MCP request
   └─ app/main.py routes
        ├─ /mcp/consumption/request → consumption/mcp_handler.py → consumption/client.py → Azure Logic Apps (Consumption)
        ├─ /mcp/standard/request    → standard/mcp_handler.py    → standard/client.py    → Azure Logic Apps (Standard)
        └─ /mcp/kudu/request        → kudu/mcp_handler.py        → kudu/client.py        → Kudu REST API (Standard)
                              ↘ shared/base_client.py for auth/session helpers
```

## Features
- FastAPI HTTP surface with health/root probes.
- MCP tool suites for Consumption, Standard, and Kudu operations.
- Azure ARM integration for Logic App lifecycle and monitoring.
- Kudu management for file/process access on Standard plans.
- Shared authentication utilities to keep per-plan clients consistent.

## Endpoints & MCP entrypoints
- `GET /health` – service health probe.
- `POST /mcp/request` – generic MCP dispatcher (tool listing/introspection).
- `POST /mcp/consumption/request` – Consumption MCP tools (list, get, trigger, create, history).
- `POST /mcp/standard/request` – Standard MCP tools (list, get, deploy, monitor).
- `POST /mcp/kudu/request` – Kudu MCP tools (file browse, commands, logs).

### MCP request payloads
- Every `tools/call` payload should include an `azure` object inside `params.arguments` that supplies `subscription_id` and `resource_group`, plus optional `tenant_id`/`client_id`/`client_secret` for service principal auth.
- When `client_secret` is not present, the server authenticates with the locally available Azure CLI/device login (`az login`) via `DefaultAzureCredential`.
- Example (Consumption):
  ```json
  {
    "method": "tools/call",
    "params": {
      "name": "get_consumption_logic_app",
      "arguments": {
        "workflow_name": "my-workflow",
        "azure": {
          "subscription_id": "<sub>",
          "resource_group": "<rg>",
          "tenant_id": "<tenant>",
          "client_id": "<app-id>"
        }
      }
    }
  }
  ```

## Authentication & environment
- MCP requests should include the Azure context for the target Logic App: `subscription_id` and `resource_group` are required; `tenant_id`/`client_id`/`client_secret` are optional.
- When a `client_secret` is supplied, the server authenticates with that service principal; otherwise it falls back to `az login`/`DefaultAzureCredential` on the host.
- Environment variables are optional and act as defaults when a request omits values: `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `LOGIC_APP_LOCATION`.
- Logging defaults to `INFO` but can be adjusted per deployment with the `LOG_LEVEL` environment variable (e.g., `DEBUG` for more verbose diagnostics).
- Server tuning knobs: `HOST` (default `localhost`), `PORT` (default `8000`), `DEBUG` (bool).

## Logging
- Application and Uvicorn logs are unified through a shared logging configuration that emits timestamped messages to stdout.
- Incoming HTTP requests are logged with method, path, status code, and duration to simplify troubleshooting.
- Set `LOG_LEVEL` to control verbosity (e.g., `DEBUG` for detailed troubleshooting, `WARNING` for quieter operation).
- **Azure Web App best practice:** enable App Service application logging/streaming so stdout/stderr from the container is captured (Portal → App Service → Logs → Application Logging) and use `az webapp log tail` for live diagnostics.

## Deployment
- **Local development**: `uv sync` then `uv run python -m app.main` with the environment above. Useful for MCP client integration tests and local Kudu calls through tunnels or dev resources.
- **Azure App Service**: Deploy the FastAPI app (e.g., via `az webapp up` or CI/CD). Provide the same environment variables in App Service settings; enable managed identity or keep the service principal secrets in Key Vault/App Settings. Expose port 8000 internally—App Service handles HTTP binding.
  - The repo includes an `application.py` shim so the default App Service gunicorn command (`gunicorn --bind=0.0.0.0 --timeout 600 application:app`) resolves the FastAPI app without needing a custom startup command.

## Additional docs
- Consumption plan details: [app/consumption/README.md](app/consumption/README.md)
- Standard plan details: [app/standard/README.md](app/standard/README.md)
- Kudu integration details: [app/kudu/README.md](app/kudu/README.md)
