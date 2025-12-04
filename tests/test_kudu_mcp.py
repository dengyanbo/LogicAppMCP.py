"""
Unit tests for KuduMCPHandler

Tests MCP protocol compliance and all Kudu operations through MCP interface.
"""

import asyncio
import json
import base64
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.kudu.mcp_handler import KuduMCPHandler


class TestKuduMCPHandler:
    """Test suite for KuduMCPHandler MCP protocol compliance"""

    @pytest.fixture
    def kudu_mcp_handler(self):
        """Create KuduMCPHandler instance for testing"""
        return KuduMCPHandler()

    @pytest.fixture
    def azure_context_payload(self):
        from app.config import settings

        settings.AZURE_SUBSCRIPTION_ID = "sub"
        settings.AZURE_RESOURCE_GROUP = "rg"
        settings.AZURE_TENANT_ID = "tenant"
        settings.AZURE_CLIENT_ID = "client"
        settings.AZURE_CLIENT_SECRET = "secret"

        return {
            "subscription_id": "sub",
            "resource_group": "rg",
            "tenant_id": "tenant",
            "client_id": "client",
            "client_secret": "secret",
        }

    @pytest.mark.asyncio
    async def test_handle_tools_list(self, kudu_mcp_handler):
        """Test tools/list method returns all available tools"""
        request = {"method": "tools/list"}

        response = await kudu_mcp_handler.handle_request(request)
        
        assert "result" in response
        assert "tools" in response["result"]
        tools = response["result"]["tools"]
        
        # Should have 30+ tools
        assert len(tools) >= 30
        
        # Check some key tools are present
        tool_names = [tool["name"] for tool in tools]
        assert "get_file" in tool_names
        assert "list_directory" in tool_names
        assert "execute_command" in tool_names
        assert "list_deployments" in tool_names
        assert "list_processes" in tool_names
        
        # Verify tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert "type" in tool["inputSchema"]
            assert "properties" in tool["inputSchema"]

    @pytest.mark.asyncio
    async def test_tools_list_includes_azure_context(self, kudu_mcp_handler):
        response = await kudu_mcp_handler.handle_request({"method": "tools/list"})
        tools = response["result"]["tools"]

        for tool in tools:
            props = tool.get("inputSchema", {}).get("properties", {})
            assert "azure_context" in props or "azure" in props
            azure_context = props.get("azure_context") or props.get("azure")
            assert azure_context.get("type") == "object"
            azure_props = azure_context.get("properties", {})
            for expected in {"subscription_id", "resource_group", "tenant_id", "client_id", "client_secret"}:
                assert expected in azure_props

    @pytest.mark.asyncio
    async def test_handle_resources_list(self, kudu_mcp_handler):
        """Test resources/list method returns available resources"""
        request = {"method": "resources/list"}
        
        response = await kudu_mcp_handler.handle_request(request)
        
        assert "result" in response
        assert "resources" in response["result"]
        resources = response["result"]["resources"]
        
        # Should have multiple resources
        assert len(resources) >= 5
        
        # Check resource structure
        for resource in resources:
            assert "uri" in resource
            assert "mimeType" in resource
            assert "name" in resource
            assert "description" in resource
            assert resource["uri"].startswith("kudu://")

    @pytest.mark.asyncio
    async def test_get_scm_info_tool(self, kudu_mcp_handler, azure_context_payload):
        """Test get_scm_info tool execution"""
        mock_scm_data = {
            "GitUrl": "https://test-app.scm.azurewebsites.net/test-app.git",
            "LocalGitUrl": "https://test-app.scm.azurewebsites.net/test-app.git"
        }
        
        with patch.object(kudu_mcp_handler.client, 'get_scm_info', return_value=mock_scm_data):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "get_scm_info",
                    "arguments": {
                        "app_name": "test-app",
                        "azure_context": azure_context_payload,
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            assert "content" in response["result"]
            content = response["result"]["content"][0]["text"]
            parsed_content = json.loads(content)
            assert parsed_content == mock_scm_data

    @pytest.mark.asyncio
    async def test_execute_command_tool(self, kudu_mcp_handler, azure_context_payload):
        """Test execute_command tool execution"""
        mock_command_result = {
            "ExitCode": 0,
            "Output": "Hello World",
            "Error": ""
        }
        
        with patch.object(kudu_mcp_handler.client, 'execute_command', return_value=mock_command_result):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "execute_command",
                    "arguments": {
                        "app_name": "test-app",
                        "command": "echo Hello World",
                        "directory": "site\\wwwroot",
                        "azure_context": azure_context_payload,
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            content = response["result"]["content"][0]["text"]
            parsed_content = json.loads(content)
            assert parsed_content == mock_command_result

    @pytest.mark.asyncio
    async def test_get_file_tool_text(self, kudu_mcp_handler, azure_context_payload):
        """Test get_file tool with text content"""
        with patch.object(kudu_mcp_handler.client, 'get_file', return_value=b"Hello from file"):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "get_file",
                    "arguments": {
                        "app_name": "test-app",
                        "file_path": "site/wwwroot/test.txt",
                        "azure_context": azure_context_payload,
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            assert response["result"]["content"][0]["text"] == "Hello from file"

    @pytest.mark.asyncio
    async def test_list_directory_tool(self, kudu_mcp_handler, azure_context_payload):
        """Test list_directory tool execution"""
        mock_files = [
            {"name": "test.txt", "size": 100, "mtime": "2025-01-01T00:00:00Z"},
            {"name": "subfolder/", "size": 0, "mtime": "2025-01-01T00:00:00Z"}
        ]
        
        with patch.object(kudu_mcp_handler.client, 'list_directory', return_value=mock_files), \
             patch.object(kudu_mcp_handler.client, '_serialize_file_info', side_effect=lambda x: x):
            
            request = {
                "method": "tools/call",
                "params": {
                    "name": "list_directory",
                    "arguments": {
                        "app_name": "test-app",
                        "dir_path": "site/wwwroot",
                        "azure_context": azure_context_payload,
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            content = response["result"]["content"][0]["text"]
            parsed_content = json.loads(content)
            assert parsed_content == mock_files

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, kudu_mcp_handler, azure_context_payload):
        """Test handling of invalid tool name"""
        request = {
            "method": "tools/call",
            "params": {
                "name": "invalid_tool",
                "arguments": {"azure_context": azure_context_payload}
            }
        }
        
        response = await kudu_mcp_handler.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_tool_execution_error(self, kudu_mcp_handler, azure_context_payload):
        """Test handling of tool execution errors"""
        with patch.object(kudu_mcp_handler.client, 'get_scm_info', side_effect=Exception("Test error")):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "get_scm_info",
                    "arguments": {"app_name": "test-app", "azure_context": azure_context_payload}
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "error" in response
            assert response["error"]["code"] == -32603
            assert "Test error" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_invalid_method(self, kudu_mcp_handler):
        """Test handling of invalid method"""
        request = {"method": "invalid/method"}
        
        response = await kudu_mcp_handler.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "not found" in response["error"]["message"]