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
    async def test_handle_resources_read(self, kudu_mcp_handler):
        """Test resources/read method"""
        request = {
            "method": "resources/read",
            "params": {"uri": "kudu://scm/info"}
        }
        
        response = await kudu_mcp_handler.handle_request(request)
        
        assert "result" in response
        assert "contents" in response["result"]

    @pytest.mark.asyncio
    async def test_handle_invalid_method(self, kudu_mcp_handler):
        """Test handling of invalid method"""
        request = {"method": "invalid/method"}
        
        response = await kudu_mcp_handler.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_get_scm_info_tool(self, kudu_mcp_handler):
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
                    "arguments": {"app_name": "test-app"}
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            assert "content" in response["result"]
            content = response["result"]["content"][0]["text"]
            parsed_content = json.loads(content)
            assert parsed_content == mock_scm_data

    @pytest.mark.asyncio
    async def test_clean_repository_tool(self, kudu_mcp_handler):
        """Test clean_repository tool execution"""
        with patch.object(kudu_mcp_handler.client, 'clean_repository', return_value="Repository cleaned successfully"):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "clean_repository",
                    "arguments": {"app_name": "test-app"}
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            assert response["result"]["content"][0]["text"] == "Repository cleaned successfully"

    @pytest.mark.asyncio
    async def test_execute_command_tool(self, kudu_mcp_handler):
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
                        "directory": "site\\wwwroot"
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            content = response["result"]["content"][0]["text"]
            parsed_content = json.loads(content)
            assert parsed_content == mock_command_result

    @pytest.mark.asyncio
    async def test_get_file_tool_text(self, kudu_mcp_handler):
        """Test get_file tool with text content"""
        with patch.object(kudu_mcp_handler.client, 'get_file', return_value=b"Hello from file"):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "get_file",
                    "arguments": {
                        "app_name": "test-app",
                        "file_path": "site/wwwroot/test.txt"
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            assert response["result"]["content"][0]["text"] == "Hello from file"

    @pytest.mark.asyncio
    async def test_get_file_tool_binary(self, kudu_mcp_handler):
        """Test get_file tool with binary content"""
        binary_content = b"\x89PNG\r\n\x1a\n"  # PNG signature
        
        with patch.object(kudu_mcp_handler.client, 'get_file', return_value=binary_content):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "get_file",
                    "arguments": {
                        "app_name": "test-app",
                        "file_path": "site/wwwroot/image.png"
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            content = response["result"]["content"][0]["text"]
            assert content.startswith("Binary file (base64):")
            # Verify base64 encoding
            b64_content = content.replace("Binary file (base64): ", "")
            decoded = base64.b64decode(b64_content)
            assert decoded == binary_content

    @pytest.mark.asyncio
    async def test_list_directory_tool(self, kudu_mcp_handler):
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
                        "dir_path": "site/wwwroot"
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            content = response["result"]["content"][0]["text"]
            parsed_content = json.loads(content)
            assert parsed_content == mock_files

    @pytest.mark.asyncio
    async def test_put_file_tool_text(self, kudu_mcp_handler):
        """Test put_file tool with text content"""
        with patch.object(kudu_mcp_handler.client, 'put_file', return_value="File uploaded successfully"):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "put_file",
                    "arguments": {
                        "app_name": "test-app",
                        "file_path": "site/wwwroot/test.txt",
                        "content": "Hello World",
                        "encoding": "text"
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            assert response["result"]["content"][0]["text"] == "File uploaded successfully"

    @pytest.mark.asyncio
    async def test_put_file_tool_base64(self, kudu_mcp_handler):
        """Test put_file tool with base64 content"""
        original_content = b"Binary data"
        b64_content = base64.b64encode(original_content).decode('ascii')
        
        with patch.object(kudu_mcp_handler.client, 'put_file', return_value="File uploaded successfully"):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "put_file",
                    "arguments": {
                        "app_name": "test-app",
                        "file_path": "site/wwwroot/binary.dat",
                        "content": b64_content,
                        "encoding": "base64"
                    }
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "result" in response
            assert response["result"]["content"][0]["text"] == "File uploaded successfully"

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, kudu_mcp_handler):
        """Test handling of invalid tool name"""
        request = {
            "method": "tools/call",
            "params": {
                "name": "invalid_tool",
                "arguments": {}
            }
        }
        
        response = await kudu_mcp_handler.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_tool_execution_error(self, kudu_mcp_handler):
        """Test handling of tool execution errors"""
        with patch.object(kudu_mcp_handler.client, 'get_scm_info', side_effect=Exception("Test error")):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "get_scm_info",
                    "arguments": {"app_name": "test-app"}
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "error" in response
            assert response["error"]["code"] == -32603
            assert "Test error" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_missing_arguments(self, kudu_mcp_handler):
        """Test handling of missing required arguments"""
        with patch.object(kudu_mcp_handler.client, 'get_scm_info', side_effect=KeyError("app_name")):
            request = {
                "method": "tools/call",
                "params": {
                    "name": "get_scm_info",
                    "arguments": {}  # Missing required app_name
                }
            }
            
            response = await kudu_mcp_handler.handle_request(request)
            
            assert "error" in response
            assert response["error"]["code"] == -32603

    @pytest.mark.asyncio
    async def test_malformed_request(self, kudu_mcp_handler):
        """Test handling of malformed requests"""
        # Request without required method
        request = {"params": {}}
        
        response = await kudu_mcp_handler.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601
