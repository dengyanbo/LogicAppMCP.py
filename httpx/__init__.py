"""Lightweight httpx compatibility shim for testing without external dependency."""
from __future__ import annotations
import json

class HTTPStatusError(Exception):
    pass

class Timeout:
    def __init__(self, timeout):
        self.timeout = timeout

class Response:
    def __init__(self, status_code: int = 200, json_data=None, text: str = "", content: bytes = b"", headers=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.text = text
        self.content = content
        self.headers = headers or {}

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPStatusError(f"HTTP {self.status_code}")

class AsyncClient:
    def __init__(self, *args, timeout=None, headers=None, **kwargs):
        self.timeout = timeout
        self.headers = headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, method: str, url: str, content=None, headers=None, params=None):
        # Return a generic successful response. Tests mock this method where behavior matters.
        body = content if isinstance(content, (str, bytes)) else json.dumps(content or {})
        return Response(status_code=200, json_data={}, text=str(body), content=(body.encode() if isinstance(body, str) else body))

    async def post(self, url: str, json=None, headers=None):
        body = json if json is not None else {}
        return Response(status_code=202, json_data=body, text=json and str(json) or "", content=b"")
