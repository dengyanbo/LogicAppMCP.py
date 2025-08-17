# Kudu MCP Handler

A comprehensive Model Context Protocol (MCP) implementation for Azure Kudu services, providing complete programmatic access to Logic App Standard management, debugging, and file operations through the Kudu REST API.

## Overview

Azure Kudu is the deployment and management engine behind Logic App Standard (and Azure App Service). This package provides complete programmatic access to Kudu operations through the MCP protocol, enabling advanced debugging, file management, and deployment operations for Logic App Standard instances.

**Based on:** [Kudu REST API Documentation](https://github.com/projectkudu/kudu/wiki/rest-api)

## Features

### 🔧 **Complete Kudu API Coverage**
- **30+ Operations** across 8 categories
- **Full REST API Implementation** - Aligned with official Kudu documentation
- **MCP 2024-11-05 Compliant** - Full protocol compliance
- **Async/Await Support** - Non-blocking operations
- **Authentication Handling** - Automatic publishing profile authentication

### 🗂️ **Virtual File System (VFS)**
- Browse Logic App files and directories
- Upload, download, and edit files
- Create and delete directories
- Binary and text file support
- Base64 encoding for binary content

### 🚀 **Deployment Management**
- View deployment history
- Redeploy previous versions
- Deploy from ZIP files or URLs
- Monitor deployment logs
- Delete deployments

### 💻 **Command Execution**
- Execute arbitrary commands
- Remote shell access
- Custom working directories
- Real-time output capture

### 📊 **Process Management**
- List running processes
- Get process details
- Kill processes
- Create process dumps for debugging

### 🔑 **SSH Key Management**
- Generate SSH key pairs
- Set private keys
- Delete SSH keys
- Public key retrieval

## Architecture

```
app/kudu/
├── __init__.py           # Package exports
├── client.py             # KuduClient implementation
├── mcp_handler.py        # MCP protocol handler
└── README.md            # This file
```

## Quick Start

### 1. Initialize the Handler

```python
from app.kudu import KuduMCPHandler

handler = KuduMCPHandler()
```

### 2. Handle MCP Requests

```python
# Example MCP request
request = {
    "method": "tools/call",
    "params": {
        "name": "list_directory",
        "arguments": {
            "app_name": "my-logicapp-standard",
            "dir_path": "site/wwwroot"
        }
    }
}

response = await handler.handle_request(request)
```

## Available Operations

### 🗂️ **Virtual File System (VFS) Operations**

| Operation | Description |
|-----------|-------------|
| `get_file` | Get file content from VFS |
| `list_directory` | List files and directories |
| `put_file` | Upload file to VFS |
| `create_directory` | Create directory |
| `delete_file` | Delete file from VFS |
| `download_directory_zip` | Download directory as ZIP |
| `upload_zip_directory` | Upload and extract ZIP |

### 🚀 **Deployment Operations**

| Operation | Description |
|-----------|-------------|
| `list_deployments` | Get deployment history |
| `get_deployment` | Get specific deployment details |
| `redeploy` | Redeploy previous deployment |
| `delete_deployment` | Delete deployment |
| `get_deployment_log` | Get deployment logs |
| `get_deployment_log_details` | Get specific log entry |
| `zip_deploy_from_url` | Deploy from ZIP URL |
| `zip_deploy_from_file` | Deploy from ZIP file |

### 💻 **Command & Process Operations**

| Operation | Description |
|-----------|-------------|
| `execute_command` | Execute arbitrary command |
| `list_processes` | List running processes |
| `get_process` | Get process details |
| `kill_process` | Kill a process |
| `create_process_dump` | Create process dump |

### 🔧 **SCM & Environment Operations**

| Operation | Description |
|-----------|-------------|
| `get_scm_info` | Get SCM repository info |
| `clean_repository` | Clean repository |
| `delete_repository` | Delete repository |
| `get_environment` | Get environment info |
| `get_settings` | Get application settings |

### 🔑 **SSH Key Operations**

| Operation | Description |
|-----------|-------------|
| `get_ssh_key` | Get or generate SSH keys |
| `set_private_key` | Set private SSH key |
| `delete_ssh_key` | Delete SSH key |

### 🏗️ **WebJobs Operations**

| Operation | Description |
|-----------|-------------|
| `list_webjobs` | List WebJobs |
| `get_webjob` | Get WebJob details |
| `start_webjob` | Start WebJob |
| `stop_webjob` | Stop WebJob |

## Usage Examples

### File Management

```bash
# List files in wwwroot
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_directory",
      "arguments": {
        "app_name": "my-logicapp",
        "dir_path": "site/wwwroot"
      }
    }
  }'

# Get file content
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_file",
      "arguments": {
        "app_name": "my-logicapp",
        "file_path": "site/wwwroot/host.json"
      }
    }
  }'

# Upload a file
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "put_file",
      "arguments": {
        "app_name": "my-logicapp",
        "file_path": "site/wwwroot/test.txt",
        "content": "Hello from Kudu MCP!",
        "encoding": "text"
      }
    }
  }'
```

### Deployment Management

```bash
# List deployments
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_deployments",
      "arguments": {
        "app_name": "my-logicapp"
      }
    }
  }'

# Deploy from ZIP URL
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "zip_deploy_from_url",
      "arguments": {
        "app_name": "my-logicapp",
        "package_uri": "https://example.com/deployment.zip",
        "is_async": true
      }
    }
  }'
```

### Command Execution

```bash
# Execute command
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "execute_command",
      "arguments": {
        "app_name": "my-logicapp",
        "command": "dir",
        "directory": "site\\wwwroot"
      }
    }
  }'

# List processes
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_processes",
      "arguments": {
        "app_name": "my-logicapp"
      }
    }
  }'
```

### Process Debugging

```bash
# Get process details
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_process",
      "arguments": {
        "app_name": "my-logicapp",
        "process_id": "1234"
      }
    }
  }'

# Create process dump
curl -X POST http://localhost:8000/mcp/kudu/request \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "create_process_dump",
      "arguments": {
        "app_name": "my-logicapp",
        "process_id": "1234",
        "dump_type": "mini"
      }
    }
  }'
```

## Configuration

### Environment Variables

The Kudu client uses the same Azure configuration as other services:

```env
# Azure Authentication
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=your-resource-group
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

### Authentication

Kudu operations require publishing profile authentication. The client automatically:

1. **Retrieves publishing profile** using Azure SDK
2. **Extracts Kudu credentials** from the profile
3. **Creates basic auth header** for Kudu API requests

### Kudu URL Format

Kudu endpoints follow the pattern:
```
https://{app-name}.scm.azurewebsites.net/api/{endpoint}
```

## Error Handling

All operations include comprehensive error handling:

- **Authentication Errors**: Automatic credential retrieval and validation
- **HTTP Errors**: Proper status code handling and error messages
- **File Encoding**: Automatic detection of text vs binary files
- **MCP Protocol Errors**: Standard error codes and responses

Example error response:
```json
{
  "error": {
    "code": -32603,
    "message": "Error executing get_file: File not found"
  }
}
```

## Security Considerations

### 🔒 **Access Control**
- Uses Azure RBAC for authentication
- Requires Logic App Contributor role or higher
- Publishing profile credentials are securely managed

### ⚠️ **Command Execution**
- `execute_command` provides full shell access
- Use with caution in production environments
- Consider implementing command whitelisting

### 📁 **File Operations**
- Full file system access within App Service sandbox
- Be careful with file deletions
- Backup important files before modifications

## Best Practices

### 🔧 **Debugging Workflows**
1. **Check processes** first to understand current state
2. **Review deployment logs** for deployment issues
3. **Examine file system** for missing or corrupted files
4. **Create process dumps** for detailed debugging

### 📊 **File Management**
1. **Use directories appropriately** - organize workflows logically
2. **Check file encoding** - handle binary vs text correctly
3. **Backup before changes** - use download_directory_zip
4. **Monitor file sizes** - large files may cause timeouts

### 🚀 **Deployment Operations**
1. **Use async deployment** for large packages
2. **Monitor deployment status** via returned URLs
3. **Clean deployments** when troubleshooting
4. **Keep deployment history** for rollback capability

## Integration with Logic Apps

### Standard Logic Apps Structure

```
site/wwwroot/
├── host.json                    # Functions host configuration
├── connections.json             # API connections
├── parameters.json              # Parameters
├── {workflow-name}/
│   ├── workflow.json           # Workflow definition
│   └── run.json               # Run configuration
├── lib/                        # Custom assemblies
└── bin/                        # System binaries
```

### Common Operations

1. **Deploy Workflow**: Upload workflow.json via `put_file`
2. **Update Connections**: Modify connections.json
3. **Debug Issues**: Check logs and process dumps
4. **Backup Workflows**: Download directories as ZIP

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Azure credentials
   - Check service principal permissions
   - Ensure Logic App exists

2. **File Not Found**
   - Verify file paths use forward slashes
   - Check if file exists via `list_directory`
   - Ensure proper case sensitivity

3. **Command Execution Fails**
   - Verify working directory exists
   - Check command syntax for Windows
   - Use absolute paths when needed

### Debug Commands

```bash
# Check environment
execute_command: "set"

# List all files
list_directory: "site"

# Check disk space
execute_command: "dir /s site"

# View log files
get_file: "LogFiles/Application/Functions/Function/{workflow}/invocations.log"
```

## Related Documentation

- [Kudu REST API Wiki](https://github.com/projectkudu/kudu/wiki/rest-api)
- [Azure App Service Kudu](https://docs.microsoft.com/en-us/azure/app-service/resources-kudu)
- [Logic App Standard Documentation](https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-overview)
- [MCP Protocol Specification](https://modelcontextprotocol.io/docs)

## Contributing

When adding new Kudu operations:

1. Add the operation to `KuduClient` in `client.py`
2. Add the tool definition to `_handle_tools_list()` in `mcp_handler.py`
3. Implement the handler in `_handle_tools_call()` in `mcp_handler.py`
4. Add appropriate error handling and serialization
5. Update this README with the new operation

## License

This implementation follows the same license as the parent LogicAppMCP project.

---

**Note**: This implementation provides comprehensive access to Azure Kudu services for Logic App Standard management and debugging. Use command execution and file operations with caution in production environments.

*Last updated: January 2025*  
*Kudu API Version: Current*  
*MCP Protocol: 2024-11-05*
