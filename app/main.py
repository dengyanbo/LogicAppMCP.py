"""
FastAPI Main Application Entry Point

Provides HTTP API interface for Logic App management and MCP server functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Dict, Any

from .config import settings
from .mcp_handler import MCPHandler
from .logicapp_client import LogicAppClient

# Create FastAPI application
app = FastAPI(
    title="Logic App MCP Server",
    description="Model Context Protocol server for Azure Logic Apps management",
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
mcp_handler = MCPHandler()
logicapp_client = LogicAppClient()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Logic App MCP Server is running", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "logicapp-mcp"}

@app.get("/logic-apps")
async def list_logic_apps():
    """List all Logic Apps"""
    try:
        apps = await logicapp_client.list_logic_apps()
        return {"logic_apps": apps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/request")
async def handle_mcp_request(request: Dict[str, Any]):
    """Handle MCP requests"""
    try:
        response = await mcp_handler.handle_request(request)
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