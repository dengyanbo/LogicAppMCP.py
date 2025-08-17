"""
Unit tests for KuduClient

Tests all Kudu REST API operations with mocked HTTP responses.
"""

import asyncio
import json
import base64
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx

from app.kudu.client import KuduClient


class TestKuduClient:
    """Test suite for KuduClient"""

    @pytest.fixture
    def kudu_client(self):
        """Create KuduClient instance for testing"""
        return KuduClient()

    @pytest.fixture
    def mock_http_response(self):
        """Create mock HTTP response"""
        response = MagicMock(spec=httpx.Response)
        response.raise_for_status.return_value = None
        response.headers = {}
        return response

    @pytest.mark.asyncio
    async def test_get_kudu_url(self, kudu_client):
        """Test Kudu URL generation"""
        app_name = "test-app"
        url = await kudu_client._get_kudu_url(app_name)
        assert url == "https://test-app.scm.azurewebsites.net"

    @pytest.mark.asyncio
    async def test_get_scm_info(self, kudu_client, mock_http_response):
        """Test SCM info retrieval"""
        mock_scm_data = {
            "GitUrl": "https://test-app.scm.azurewebsites.net/test-app.git",
            "LocalGitUrl": "https://test-app.scm.azurewebsites.net/test-app.git"
        }
        mock_http_response.json.return_value = mock_scm_data
        
        with patch.object(kudu_client, '_kudu_request', return_value=mock_http_response):
            result = await kudu_client.get_scm_info("test-app")
            assert result == mock_scm_data

    @pytest.mark.asyncio
    async def test_clean_repository(self, kudu_client, mock_http_response):
        """Test repository cleaning"""
        with patch.object(kudu_client, '_kudu_request', return_value=mock_http_response):
            result = await kudu_client.clean_repository("test-app")
            assert result == "Repository cleaned successfully"

    @pytest.mark.asyncio
    async def test_execute_command(self, kudu_client, mock_http_response):
        """Test command execution"""
        mock_command_result = {
            "ExitCode": 0,
            "Output": "Hello World",
            "Error": ""
        }
        mock_http_response.json.return_value = mock_command_result
        
        with patch.object(kudu_client, '_kudu_request', return_value=mock_http_response):
            result = await kudu_client.execute_command("test-app", "echo Hello World", "site\\wwwroot")
            assert result == mock_command_result

    @pytest.mark.asyncio
    async def test_get_file(self, kudu_client, mock_http_response):
        """Test file retrieval"""
        file_content = b"Hello from file"
        mock_http_response.content = file_content
        
        with patch.object(kudu_client, '_kudu_request', return_value=mock_http_response):
            result = await kudu_client.get_file("test-app", "site/wwwroot/test.txt")
            assert result == file_content

    @pytest.mark.asyncio
    async def test_list_directory(self, kudu_client, mock_http_response):
        """Test directory listing"""
        mock_files = [
            {"name": "test.txt", "size": 100, "mtime": "2025-01-01T00:00:00Z"},
            {"name": "subfolder/", "size": 0, "mtime": "2025-01-01T00:00:00Z"}
        ]
        mock_http_response.json.return_value = mock_files
        
        with patch.object(kudu_client, '_kudu_request', return_value=mock_http_response):
            result = await kudu_client.list_directory("test-app", "site/wwwroot")
            assert result == mock_files

    @pytest.mark.asyncio
    async def test_put_file_text(self, kudu_client, mock_http_response):
        """Test file upload with text content"""
        with patch.object(kudu_client, '_kudu_request', return_value=mock_http_response):
            result = await kudu_client.put_file("test-app", "site/wwwroot/test.txt", "Hello World")
            assert result == "File site/wwwroot/test.txt uploaded successfully"

    @pytest.mark.asyncio
    async def test_list_deployments(self, kudu_client, mock_http_response):
        """Test deployment listing"""
        mock_deployments = [
            {
                "id": "deployment-1",
                "status": 4,
                "message": "Deployment successful",
                "author": "test-user",
                "start_time": "2025-01-01T00:00:00Z"
            }
        ]
        mock_http_response.json.return_value = mock_deployments
        
        with patch.object(kudu_client, '_kudu_request', return_value=mock_http_response):
            result = await kudu_client.list_deployments("test-app")
            assert result == mock_deployments

    @pytest.mark.asyncio
    async def test_list_processes(self, kudu_client, mock_http_response):
        """Test process listing"""
        mock_processes = [
            {
                "id": 1234,
                "name": "w3wp",
                "description": "IIS Worker Process",
                "fileName": "w3wp.exe"
            }
        ]
        mock_http_response.json.return_value = mock_processes
        
        with patch.object(kudu_client, '_kudu_request', return_value=mock_http_response):
            result = await kudu_client.list_processes("test-app")
            assert result == mock_processes

    def test_serialize_file_info(self):
        """Test file info serialization"""
        client = KuduClient()
        file_info = {
            "name": "test.txt",
            "size": 100,
            "mtime": "2025-01-01T00:00:00Z",
            "mime": "text/plain",
            "href": "/api/vfs/test.txt",
            "path": "/test.txt"
        }
        
        result = client._serialize_file_info(file_info)
        assert result == file_info

    def test_serialize_deployment_info(self):
        """Test deployment info serialization"""
        client = KuduClient()
        deployment = {
            "id": "deployment-1",
            "status": 4,
            "message": "Success",
            "author": "user",
            "deployer": "git",
            "author_email": "user@example.com",
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-01T00:01:00Z",
            "active": True,
            "details": "https://example.com/details"
        }
        
        result = client._serialize_deployment_info(deployment)
        assert result == deployment