"""
FastAPI Main Application Entry Point

Provides HTTP API interface for Logic App management and MCP server functionality
"""

import logging
import time
from fastapi import FastAPI, HTTPException, Request
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
from .logging_config import configure_logging, get_logging_config


configure_logging()
logger = logging.getLogger(__name__)

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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log inbound requests with duration and status code."""
    start_time = time.perf_counter()
    logger.info("Received request", extra={"path": request.url.path, "method": request.method})

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(
            "Request failed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "duration_ms": round(duration_ms, 2),
            },
        )
        raise

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "Request completed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response

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
        logger.info("Listing all Logic Apps")
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
        logger.exception("Failed to list all Logic Apps")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logic-apps/consumption")
async def list_consumption_logic_apps():
    """List Consumption Logic Apps only"""
    try:
        logger.info("Listing Consumption Logic Apps")
        apps = await consumption_client.list_logic_apps()
        return {"consumption_logic_apps": apps}
    except Exception as e:
        logger.exception("Failed to list Consumption Logic Apps")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logic-apps/standard")
async def list_standard_logic_apps():
    """List Standard Logic Apps only"""
    try:
        logger.info("Listing Standard Logic Apps")
        apps = await standard_client.list_logic_apps()
        return {"standard_logic_apps": apps}
    except Exception as e:
        logger.exception("Failed to list Standard Logic Apps")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/consumption/request")
async def handle_consumption_mcp_request(request: Dict[str, Any]):
    """Handle MCP requests for Consumption Logic Apps"""
    try:
        logger.info(
            "Handling consumption MCP request",
            extra={"method": request.get("method"), "tool": request.get("params", {}).get("name")},
        )
        response = await consumption_mcp_handler.handle_request(request)
        return response
    except Exception as e:
        logger.exception("Failed to process consumption MCP request")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/standard/request")
async def handle_standard_mcp_request(request: Dict[str, Any]):
    """Handle MCP requests for Standard Logic Apps"""
    try:
        logger.info(
            "Handling standard MCP request",
            extra={"method": request.get("method"), "tool": request.get("params", {}).get("name")},
        )
        response = await standard_mcp_handler.handle_request(request)
        return response
    except Exception as e:
        logger.exception("Failed to process standard MCP request")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/kudu/request")
async def handle_kudu_mcp_request(request: Dict[str, Any]):
    """Handle MCP requests for Kudu services"""
    try:
        logger.info(
            "Handling Kudu MCP request",
            extra={"method": request.get("method"), "tool": request.get("params", {}).get("name")},
        )
        response = await kudu_mcp_handler.handle_request(request)
        return response
    except Exception as e:
        logger.exception("Failed to process Kudu MCP request")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/request")
async def handle_generic_mcp_request(request: Dict[str, Any]):
    """Handle generic MCP requests (routes to consumption by default)"""
    try:
        logger.info(
            "Handling generic MCP request",
            extra={"method": request.get("method"), "tool": request.get("params", {}).get("name")},
        )
        response = await consumption_mcp_handler.handle_request(request)
        return response
    except Exception as e:
        logger.exception("Failed to process generic MCP request")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Start server"""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=get_logging_config(),
    )

if __name__ == "__main__":
    main()