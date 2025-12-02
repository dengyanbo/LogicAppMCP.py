# Logic App MCP Server

FastAPI-based Model Context Protocol (MCP) server that lets MCP clients manage Azure Logic Apps (Consumption and Standard) and Kudu via a consistent HTTP surface.

## Quickstart (one screen)
```bash
git clone <repository-url>
cd logicappmcp.py
uv sync

# minimal environment (service principal)
cat > .env <<'EOF'
AZURE_SUBSCRIPTION_ID=...
AZURE_RESOURCE_GROUP=...
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
EOF

uv run python -m app.main &

curl http://localhost:8000/health            # health
curl -H "Content-Type: application/json" \
  -d '{"method":"tools/list","params":{}}' http://localhost:8000/mcp/request
curl -H "Content-Type: application/json" \
  -d '{"method":"tools/list","params":{}}' http://localhost:8000/mcp/consumption/request
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

## Environment
- Create a `.env` file or set variables via your process manager.
- Required Azure credentials: `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`.
- Optional server tuning: `HOST` (default `localhost`), `PORT` (default `8000`), `DEBUG` (bool), `LOGIC_APP_LOCATION` (default region for new workflows).

## Deployment
- **Local development**: `uv sync` then `uv run python -m app.main` with the environment above. Useful for MCP client integration tests and local Kudu calls through tunnels or dev resources.
- **Azure App Service**: Deploy the FastAPI app (e.g., via `az webapp up` or CI/CD). Provide the same environment variables in App Service settings; enable managed identity or keep the service principal secrets in Key Vault/App Settings. Expose port 8000 internally—App Service handles HTTP binding.

## Additional docs
- Consumption plan details: [app/consumption/README.md](app/consumption/README.md)
- Standard plan details: [app/standard/README.md](app/standard/README.md)
- Kudu integration details: [app/kudu/README.md](app/kudu/README.md)
