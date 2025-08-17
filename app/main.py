"""
FastAPI Main Application Entry Point

Provides HTTP API interface for Logic App management and MCP server functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Dict, Any

from .config import settings
from .consumption.mcp_handler import ConsumptionMCPHandler
from .standard.mcp_handler import StandardMCPHandler
from .kudu.mcp_handler import KuduMCPHandler
from .consumption.client import ConsumptionLogicAppClient
from .standard.client import StandardLogicAppClient
from .kudu.client import KuduClient

# Create FastAPI application
app = FastAPI(
    title="Logic App MCP Server",
    description="Model Context Protocol server for Azure Logic Apps management with Kudu services",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
consumption_mcp_handler = ConsumptionMCPHandler()
standard_mcp_handler = StandardMCPHandler()
kudu_mcp_handler = KuduMCPHandler()
consumption_client = ConsumptionLogicAppClient()
standard_client = StandardLogicAppClient()
kudu_client = KuduClient()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Logic App MCP Server is running", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "logicapp-mcp"}

@app.get("/logic-apps")
async def list_all_logic_apps():
    """List all Logic Apps (both Consumption and Standard)"""
    try:
        consumption_apps = await consumption_client.list_logic_apps()
        standard_apps = await standard_client.list_logic_apps()
        # De-duplicate by resource id
        by_id: Dict[str, Dict[str, Any]] = {}
        for app in consumption_apps + standard_apps:
            app_id = app.get("id") or app.get("name")
            if app_id and app_id not in by_id:
                by_id[app_id] = app
        return {
            "consumption_logic_apps": consumption_apps,
            "standard_logic_apps": standard_apps,
            "total_count": len(by_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logic-apps/consumption")
async def list_consumption_logic_apps():
    """List Consumption Logic Apps only"""
    try:
        apps = await consumption_client.list_logic_apps()
        return {"consumption_logic_apps": apps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logic-apps/standard")
async def list_standard_logic_apps():
    """List Standard Logic Apps only"""
    try:
        apps = await standard_client.list_logic_apps()
        return {"standard_logic_apps": apps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/consumption/request")
async def handle_consumption_mcp_request(request: Dict[str, Any]):
    """Handle MCP requests for Consumption Logic Apps"""
    try:
        response = await consumption_mcp_handler.handle_request(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/standard/request")
async def handle_standard_mcp_request(request: Dict[str, Any]):
    """Handle MCP requests for Standard Logic Apps"""
    try:
        response = await standard_mcp_handler.handle_request(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/kudu/request")
async def handle_kudu_mcp_request(request: Dict[str, Any]):
    """Handle MCP requests for Kudu services"""
    try:
        response = await kudu_mcp_handler.handle_request(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/request")
async def handle_generic_mcp_request(request: Dict[str, Any]):
    """Handle generic MCP requests (routes to consumption by default)"""
    try:
        response = await consumption_mcp_handler.handle_request(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Start server"""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

if __name__ == "__main__":
    main()