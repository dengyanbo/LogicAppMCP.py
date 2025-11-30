"""
Configuration Management

Manages Azure credentials, server settings, and other configuration information
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Configuration"""
    
    # Server configuration
    HOST: str = "localhost"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Azure configuration
    AZURE_SUBSCRIPTION_ID: Optional[str] = "test-sub-id"
    AZURE_RESOURCE_GROUP: Optional[str] = "test-rg"
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    
    # Logic App configuration
    LOGIC_APP_LOCATION: str = "East US"
    
    # MCP configuration
    MCP_SERVER_NAME: str = "logicapp-mcp"
    MCP_SERVER_VERSION: str = "0.1.0"
    
    # Pydantic v2: replace class-based Config with SettingsConfigDict
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    def get_azure_credentials(self) -> dict:
        """Get Azure authentication credentials"""
        return {
            "subscription_id": self.AZURE_SUBSCRIPTION_ID,
            "resource_group": self.AZURE_RESOURCE_GROUP,
            "tenant_id": self.AZURE_TENANT_ID,
            "client_id": self.AZURE_CLIENT_ID,
            "client_secret": self.AZURE_CLIENT_SECRET,
        }
    
    def validate_azure_config(self) -> bool:
        """Validate if Azure configuration is complete"""
        required_fields = [
            self.AZURE_SUBSCRIPTION_ID,
            self.AZURE_RESOURCE_GROUP,
            self.AZURE_TENANT_ID,
            self.AZURE_CLIENT_ID,
            self.AZURE_CLIENT_SECRET,
        ]
        return all(field is not None for field in required_fields)


# Global configuration instance
settings = Settings()