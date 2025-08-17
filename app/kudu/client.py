"""
Kudu Client Implementation

Provides comprehensive access to Azure Kudu REST API for Logic App Standard
management, debugging, and file operations.

Based on: https://github.com/projectkudu/kudu/wiki/rest-api
"""

import asyncio
import json
import os
import zipfile
from io import BytesIO
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from azure.identity import DefaultAzureCredential

from ..config import settings
from ..shared.base_client import BaseLogicAppClient


class KuduClient(BaseLogicAppClient):
    """
    Azure Kudu REST API Client
    
    Provides access to Kudu services for Logic App Standard management,
    including file system operations, deployment management, and debugging tools.
    """

    def __init__(self):
        """Initialize Kudu client with Azure credentials"""
        super().__init__()
        self.kudu_base_url: Optional[str] = None
        self.kudu_credentials: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper authentication"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                headers={
                    "User-Agent": "LogicApp-MCP-Kudu-Client/1.0",
                    "Accept": "application/json",
                }
            )
        return self._http_client

    async def _get_kudu_url(self, app_name: str) -> str:
        """Get Kudu SCM URL for Logic App Standard"""
        if not self.kudu_base_url:
            # Standard Logic Apps use App Service hosting with SCM endpoints
            self.kudu_base_url = f"https://{app_name}.scm.azurewebsites.net"
        return self.kudu_base_url

    async def _get_kudu_credentials(self, app_name: str) -> str:
        """Get Kudu authentication credentials (publishing profile)"""
        try:
            # Get publishing profile for authentication
            from azure.mgmt.web import WebSiteManagementClient
            
            credential = DefaultAzureCredential()
            web_client = WebSiteManagementClient(credential, settings.AZURE_SUBSCRIPTION_ID)
            
            # Get publishing profile
            profile = web_client.web_apps.list_publishing_profile_xml_with_secrets(
                resource_group_name=settings.AZURE_RESOURCE_GROUP,
                name=app_name
            )
            
            # Parse profile to get Kudu credentials
            import xml.etree.ElementTree as ET
            root = ET.fromstring(profile)
            
            # Find the SCM publishing profile
            for publish_profile in root.findall('.//publishProfile'):
                if publish_profile.get('publishMethod') == 'MSDeploy':
                    username = publish_profile.get('userName')
                    password = publish_profile.get('userPWD')
                    
                    # Create basic auth string
                    import base64
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    return f"Basic {credentials}"
            
            raise Exception("Could not find Kudu credentials in publishing profile")
            
        except Exception as e:
            raise Exception(f"Failed to get Kudu credentials: {str(e)}")

    async def _kudu_request(
        self,
        app_name: str,
        method: str,
        endpoint: str,
        data: Optional[Union[Dict, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make authenticated request to Kudu API"""
        try:
            kudu_url = await self._get_kudu_url(app_name)
            credentials = await self._get_kudu_credentials(app_name)
            
            client = await self._get_http_client()
            url = urljoin(kudu_url, endpoint)
            
            request_headers = {
                "Authorization": credentials,
                **(headers or {})
            }
            
            if isinstance(data, dict):
                request_headers["Content-Type"] = "application/json"
                data = json.dumps(data)
            
            response = await client.request(
                method=method,
                url=url,
                content=data,
                headers=request_headers,
                params=params
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"Kudu API request failed: {str(e)}")

    # SCM Information Operations
    async def get_scm_info(self, app_name: str) -> Dict[str, Any]:
        """Get SCM repository information"""
        response = await self._kudu_request(app_name, "GET", "/api/scm/info")
        response.raise_for_status()
        return response.json()

    async def clean_repository(self, app_name: str) -> str:
        """Clean repository using 'git clean -xdff'"""
        response = await self._kudu_request(app_name, "POST", "/api/scm/clean")
        response.raise_for_status()
        return "Repository cleaned successfully"

    async def delete_repository(self, app_name: str) -> str:
        """Delete the repository"""
        response = await self._kudu_request(app_name, "DELETE", "/api/scm")
        response.raise_for_status()
        return "Repository deleted successfully"

    # Command Execution
    async def execute_command(self, app_name: str, command: str, directory: str = "site\\wwwroot") -> Dict[str, Any]:
        """Execute arbitrary command and return output"""
        data = {
            "command": command,
            "dir": directory
        }
        response = await self._kudu_request(app_name, "POST", "/api/command", data=data)
        response.raise_for_status()
        return response.json()

    # VFS (Virtual File System) Operations
    async def get_file(self, app_name: str, file_path: str) -> bytes:
        """Get file content from VFS"""
        endpoint = f"/api/vfs/{file_path}"
        response = await self._kudu_request(app_name, "GET", endpoint)
        response.raise_for_status()
        return response.content

    async def list_directory(self, app_name: str, dir_path: str) -> List[Dict[str, Any]]:
        """List files in directory"""
        endpoint = f"/api/vfs/{dir_path}/"
        response = await self._kudu_request(app_name, "GET", endpoint)
        response.raise_for_status()
        return response.json()

    async def put_file(self, app_name: str, file_path: str, content: Union[str, bytes]) -> str:
        """Upload file to VFS"""
        endpoint = f"/api/vfs/{file_path}"
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        headers = {"If-Match": "*"}  # Disable ETag check
        response = await self._kudu_request(app_name, "PUT", endpoint, data=content, headers=headers)
        response.raise_for_status()
        return f"File {file_path} uploaded successfully"

    async def create_directory(self, app_name: str, dir_path: str) -> str:
        """Create directory in VFS"""
        endpoint = f"/api/vfs/{dir_path}/"
        response = await self._kudu_request(app_name, "PUT", endpoint)
        response.raise_for_status()
        return f"Directory {dir_path} created successfully"

    async def delete_file(self, app_name: str, file_path: str) -> str:
        """Delete file from VFS"""
        endpoint = f"/api/vfs/{file_path}"
        headers = {"If-Match": "*"}  # Disable ETag check
        response = await self._kudu_request(app_name, "DELETE", endpoint, headers=headers)
        response.raise_for_status()
        return f"File {file_path} deleted successfully"

    # Zip Operations
    async def download_directory_as_zip(self, app_name: str, dir_path: str) -> bytes:
        """Download directory as zip file"""
        endpoint = f"/api/zip/{dir_path}/"
        response = await self._kudu_request(app_name, "GET", endpoint)
        response.raise_for_status()
        return response.content

    async def upload_zip_to_directory(self, app_name: str, dir_path: str, zip_content: bytes) -> str:
        """Upload and extract zip file to directory"""
        endpoint = f"/api/zip/{dir_path}/"
        headers = {"Content-Type": "application/zip"}
        response = await self._kudu_request(app_name, "PUT", endpoint, data=zip_content, headers=headers)
        response.raise_for_status()
        return f"Zip file extracted to {dir_path} successfully"

    # Deployment Operations
    async def list_deployments(self, app_name: str) -> List[Dict[str, Any]]:
        """Get list of all deployments"""
        response = await self._kudu_request(app_name, "GET", "/api/deployments")
        response.raise_for_status()
        return response.json()

    async def get_deployment(self, app_name: str, deployment_id: str) -> Dict[str, Any]:
        """Get specific deployment details"""
        endpoint = f"/api/deployments/{deployment_id}"
        response = await self._kudu_request(app_name, "GET", endpoint)
        response.raise_for_status()
        return response.json()

    async def redeploy(self, app_name: str, deployment_id: Optional[str] = None, clean: bool = False, need_file_update: bool = True) -> str:
        """Redeploy a current or previous deployment"""
        endpoint = f"/api/deployments/{deployment_id}" if deployment_id else "/api/deployments"
        data = {
            "clean": clean,
            "needFileUpdate": need_file_update
        }
        response = await self._kudu_request(app_name, "PUT", endpoint, data=data)
        response.raise_for_status()
        return f"Redeployment {'of ' + deployment_id if deployment_id else ''} initiated successfully"

    async def delete_deployment(self, app_name: str, deployment_id: str) -> str:
        """Delete a deployment"""
        endpoint = f"/api/deployments/{deployment_id}"
        response = await self._kudu_request(app_name, "DELETE", endpoint)
        response.raise_for_status()
        return f"Deployment {deployment_id} deleted successfully"

    async def get_deployment_log(self, app_name: str, deployment_id: str) -> List[Dict[str, Any]]:
        """Get deployment log entries"""
        endpoint = f"/api/deployments/{deployment_id}/log"
        response = await self._kudu_request(app_name, "GET", endpoint)
        response.raise_for_status()
        return response.json()

    async def get_deployment_log_details(self, app_name: str, deployment_id: str, log_id: str) -> Dict[str, Any]:
        """Get specific deployment log entry details"""
        endpoint = f"/api/deployments/{deployment_id}/log/{log_id}"
        response = await self._kudu_request(app_name, "GET", endpoint)
        response.raise_for_status()
        return response.json()

    # Zip Deployment
    async def zip_deploy_from_url(self, app_name: str, package_uri: str, is_async: bool = True) -> Dict[str, Any]:
        """Deploy from zip URL"""
        endpoint = "/api/zipdeploy"
        params = {"isAsync": "true"} if is_async else None
        data = {"packageUri": package_uri}
        headers = {"Content-Type": "application/json"}
        
        response = await self._kudu_request(app_name, "PUT", endpoint, data=data, headers=headers, params=params)
        response.raise_for_status()
        
        result = {"message": "Zip deployment initiated successfully"}
        if is_async and "Location" in response.headers:
            result["deployment_status_url"] = response.headers["Location"]
        
        return result

    async def zip_deploy_from_file(self, app_name: str, zip_content: bytes) -> str:
        """Deploy from zip file content"""
        endpoint = "/api/zipdeploy"
        headers = {"Content-Type": "application/zip"}
        response = await self._kudu_request(app_name, "POST", endpoint, data=zip_content, headers=headers)
        response.raise_for_status()
        return "Zip deployment completed successfully"

    # SSH Key Operations
    async def get_ssh_key(self, app_name: str, ensure_public_key: bool = True) -> Dict[str, Any]:
        """Get or generate SSH keys"""
        params = {"ensurePublicKey": "1"} if ensure_public_key else None
        response = await self._kudu_request(app_name, "GET", "/api/sshkey", params=params)
        response.raise_for_status()
        return response.json()

    async def set_private_key(self, app_name: str, private_key: str) -> str:
        """Set private SSH key"""
        response = await self._kudu_request(app_name, "PUT", "/api/sshkey", data=private_key)
        response.raise_for_status()
        return "Private SSH key set successfully"

    async def delete_ssh_key(self, app_name: str) -> str:
        """Delete SSH key"""
        response = await self._kudu_request(app_name, "DELETE", "/api/sshkey")
        response.raise_for_status()
        return "SSH key deleted successfully"

    # Environment Operations
    async def get_environment(self, app_name: str) -> Dict[str, Any]:
        """Get environment information"""
        response = await self._kudu_request(app_name, "GET", "/api/environment")
        response.raise_for_status()
        return response.json()

    async def get_settings(self, app_name: str) -> Dict[str, Any]:
        """Get application settings"""
        response = await self._kudu_request(app_name, "GET", "/api/settings")
        response.raise_for_status()
        return response.json()

    # Process Operations
    async def list_processes(self, app_name: str) -> List[Dict[str, Any]]:
        """List running processes"""
        response = await self._kudu_request(app_name, "GET", "/api/processes")
        response.raise_for_status()
        return response.json()

    async def get_process(self, app_name: str, process_id: str) -> Dict[str, Any]:
        """Get specific process details"""
        endpoint = f"/api/processes/{process_id}"
        response = await self._kudu_request(app_name, "GET", endpoint)
        response.raise_for_status()
        return response.json()

    async def kill_process(self, app_name: str, process_id: str) -> str:
        """Kill a process"""
        endpoint = f"/api/processes/{process_id}"
        response = await self._kudu_request(app_name, "DELETE", endpoint)
        response.raise_for_status()
        return f"Process {process_id} killed successfully"

    async def create_process_dump(self, app_name: str, process_id: str, dump_type: str = "mini") -> bytes:
        """Create process dump"""
        endpoint = f"/api/processes/{process_id}/dump"
        params = {"dumpType": dump_type}
        response = await self._kudu_request(app_name, "GET", endpoint, params=params)
        response.raise_for_status()
        return response.content

    # WebJobs Operations
    async def list_webjobs(self, app_name: str) -> List[Dict[str, Any]]:
        """List WebJobs"""
        response = await self._kudu_request(app_name, "GET", "/api/webjobs")
        response.raise_for_status()
        return response.json()

    async def get_webjob(self, app_name: str, job_name: str) -> Dict[str, Any]:
        """Get WebJob details"""
        endpoint = f"/api/webjobs/{job_name}"
        response = await self._kudu_request(app_name, "GET", endpoint)
        response.raise_for_status()
        return response.json()

    async def start_webjob(self, app_name: str, job_name: str) -> str:
        """Start a WebJob"""
        endpoint = f"/api/webjobs/{job_name}/start"
        response = await self._kudu_request(app_name, "POST", endpoint)
        response.raise_for_status()
        return f"WebJob {job_name} started successfully"

    async def stop_webjob(self, app_name: str, job_name: str) -> str:
        """Stop a WebJob"""
        endpoint = f"/api/webjobs/{job_name}/stop"
        response = await self._kudu_request(app_name, "POST", endpoint)
        response.raise_for_status()
        return f"WebJob {job_name} stopped successfully"

    # Utility Methods
    def _serialize_file_info(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize file information"""
        return {
            "name": file_info.get("name"),
            "size": file_info.get("size"),
            "mtime": file_info.get("mtime"),
            "mime": file_info.get("mime"),
            "href": file_info.get("href"),
            "path": file_info.get("path"),
        }

    def _serialize_deployment_info(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize deployment information"""
        return {
            "id": deployment.get("id"),
            "status": deployment.get("status"),
            "message": deployment.get("message"),
            "author": deployment.get("author"),
            "deployer": deployment.get("deployer"),
            "author_email": deployment.get("author_email"),
            "start_time": deployment.get("start_time"),
            "end_time": deployment.get("end_time"),
            "active": deployment.get("active"),
            "details": deployment.get("details"),
        }

    def _serialize_process_info(self, process: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize process information"""
        return {
            "id": process.get("id"),
            "name": process.get("name"),
            "description": process.get("description"),
            "href": process.get("href"),
            "file_name": process.get("file_name"),
            "command_line": process.get("command_line"),
            "user_name": process.get("user_name"),
            "working_directory": process.get("working_directory"),
            "environment_variables": process.get("environment_variables"),
        }

    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
