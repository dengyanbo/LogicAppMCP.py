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
    def azure_context(self):
        """Shared Azure context for tests"""
        return {
            "subscription_id": "context-sub",
            "resource_group": "context-rg",
            "tenant_id": None,
            "client_id": None,
            "client_secret": None,
        }

    @pytest.fixture
    def kudu_client(self, azure_context):
        """Create KuduClient instance for testing"""
        return KuduClient(azure_context=azure_context)

    @pytest.fixture
    def mock_http_response(self):
        """Create mock HTTP response"""
        response = MagicMock(spec=httpx.Response)
        response.raise_for_status.return_value = None
        response.headers = {}
        return response

    @pytest.fixture
    def mock_publishing_profile(self):
        """Mock publishing profile XML"""
        return '''<?xml version="1.0" encoding="utf-8"?>
        <publishData>
            <publishProfile publishMethod="MSDeploy" userName="$test-app" userPWD="test-password" />
        </publishData>'''

    @pytest.mark.asyncio
    async def test_get_kudu_url(self, kudu_client):
        """Test Kudu URL generation"""
        app_name = "test-app"
        url = await kudu_client._get_kudu_url(app_name)
        assert url == "https://test-app.scm.azurewebsites.net"

    @patch('azure.mgmt.web.WebSiteManagementClient')
    @patch('app.kudu.client.DefaultAzureCredential')
    @pytest.mark.asyncio
    async def test_get_kudu_credentials(self, mock_credential, mock_web_client, kudu_client, mock_publishing_profile):
        """Test Kudu credentials retrieval"""
        # Mock the web client and publishing profile
        mock_web_instance = mock_web_client.return_value
        mock_web_instance.web_apps.list_publishing_profile_xml_with_secrets.return_value = mock_publishing_profile
        
        credentials = await kudu_client._get_kudu_credentials("test-app")
        
        # Verify basic auth format
        assert credentials.startswith("Basic ")
        
        # Decode and verify credentials
        encoded_creds = credentials.replace("Basic ", "")
        decoded_creds = base64.b64decode(encoded_creds).decode()
        assert decoded_creds == "$test-app:test-password"

    @patch('app.kudu.client.DefaultAzureCredential')
    @patch('app.kudu.client.ClientSecretCredential')
    @patch('azure.mgmt.web.WebSiteManagementClient')
    @pytest.mark.asyncio
    async def test_get_kudu_credentials_with_context(self, mock_web_client, mock_client_cred, mock_default_cred, kudu_client, mock_publishing_profile):
        """Ensure provided Azure context drives credential creation and subscription selection"""
        azure_context = {
            "subscription_id": "context-sub",
            "resource_group": "context-rg",
            "tenant_id": "tenant",
            "client_id": "client",
            "client_secret": "secret",
        }

        mock_web_instance = mock_web_client.return_value
        mock_web_instance.web_apps.list_publishing_profile_xml_with_secrets.return_value = mock_publishing_profile

        await kudu_client._get_kudu_credentials("test-app", azure_context)

        mock_client_cred.assert_called_once_with(tenant_id="tenant", client_id="client", client_secret="secret")
        mock_default_cred.assert_not_called()
        mock_web_client.assert_called_once_with(mock_client_cred.return_value, "context-sub")

    @patch('app.kudu.client.KuduClient._kudu_request')
    @pytest.mark.asyncio
    async def test_get_scm_info(self, mock_request, kudu_client, mock_http_response):
        """Test SCM info retrieval"""
        mock_scm_data = {
            "GitUrl": "https://test-app.scm.azurewebsites.net/test-app.git",
            "LocalGitUrl": "https://test-app.scm.azurewebsites.net/test-app.git"
        }
        mock_http_response.json.return_value = mock_scm_data
        mock_request.return_value = mock_http_response

        result = await kudu_client.get_scm_info("test-app")

        assert result == mock_scm_data
        mock_request.assert_called_once_with("test-app", "GET", "/api/scm/info", azure_context=kudu_client.azure_context)

    @patch('app.kudu.client.KuduClient._kudu_request')
    @pytest.mark.asyncio
    async def test_clean_repository(self, mock_request, kudu_client, mock_http_response):
        """Test repository cleaning"""
        mock_request.return_value = mock_http_response

        result = await kudu_client.clean_repository("test-app")

        assert result == "Repository cleaned successfully"
        mock_request.assert_called_once_with("test-app", "POST", "/api/scm/clean", azure_context=kudu_client.azure_context)

    @patch('app.kudu.client.KuduClient._kudu_request')
    @pytest.mark.asyncio
    async def test_delete_repository(self, mock_request, kudu_client, mock_http_response):
        """Test repository deletion"""
        mock_request.return_value = mock_http_response

        result = await kudu_client.delete_repository("test-app")

        assert result == "Repository deleted successfully"
        mock_request.assert_called_once_with("test-app", "DELETE", "/api/scm", azure_context=kudu_client.azure_context)

    @patch('app.kudu.client.KuduClient._kudu_request')
    @pytest.mark.asyncio
    async def test_execute_command(self, mock_request, kudu_client, mock_http_response):
        """Test command execution"""
        mock_command_result = {
            "ExitCode": 0,
            "Output": "Hello World",
            "Error": ""
        }
        mock_http_response.json.return_value = mock_command_result
        mock_request.return_value = mock_http_response

        result = await kudu_client.execute_command("test-app", "echo Hello World", "site\\wwwroot")

        assert result == mock_command_result
        mock_request.assert_called_once_with(
            "test-app",
            "POST",
            "/api/command",
            data={"command": "echo Hello World", "dir": "site\\wwwroot"},
            azure_context=kudu_client.azure_context,
        )

    @patch('app.kudu.client.KuduClient._kudu_request')
    @pytest.mark.asyncio
    async def test_get_file(self, mock_request, kudu_client, mock_http_response):
        """Test file retrieval"""
        file_content = b"Hello from file"
        mock_http_response.content = file_content
        mock_request.return_value = mock_http_response

        result = await kudu_client.get_file("test-app", "site/wwwroot/test.txt")

        assert result == file_content
        mock_request.assert_called_once_with("test-app", "GET", "/api/vfs/site/wwwroot/test.txt", azure_context=kudu_client.azure_context)

    @patch('app.kudu.client.KuduClient._kudu_request')
    @pytest.mark.asyncio
    async def test_list_directory(self, mock_request, kudu_client, mock_http_response):
        """Test directory listing"""
        mock_files = [
            {"name": "test.txt", "size": 100, "mtime": "2025-01-01T00:00:00Z"},
            {"name": "subfolder/", "size": 0, "mtime": "2025-01-01T00:00:00Z"}
        ]
        mock_http_response.json.return_value = mock_files
        mock_request.return_value = mock_http_response

        result = await kudu_client.list_directory("test-app", "site/wwwroot")

        assert result == mock_files
        mock_request.assert_called_once_with("test-app", "GET", "/api/vfs/site/wwwroot/", azure_context=kudu_client.azure_context)

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

    def test_serialize_process_info(self):
        """Test process info serialization"""
        client = KuduClient()
        process = {
            "id": 1234,
            "name": "w3wp",
            "description": "IIS Worker Process",
            "href": "/api/processes/1234",
            "file_name": "w3wp.exe",
            "command_line": "w3wp.exe -ap",
            "user_name": "IIS APPPOOL\\test",
            "working_directory": "C:\\",
            "environment_variables": {"PATH": "C:\\"}
        }
        
        result = client._serialize_process_info(process)
        
        assert result == process
