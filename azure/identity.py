"""Lightweight stubs for azure.identity classes used in tests."""

class DefaultAzureCredential:
    def __init__(self, *args, **kwargs):
        pass

class ClientSecretCredential:
    def __init__(self, *args, **kwargs):
        self.tenant_id = kwargs.get("tenant_id")
        self.client_id = kwargs.get("client_id")
        self.client_secret = kwargs.get("client_secret")
