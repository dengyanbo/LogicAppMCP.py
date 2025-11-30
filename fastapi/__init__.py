"""Minimal FastAPI stubs for unit testing without external dependency."""
import asyncio
import json
from typing import Any, Callable, Dict, Tuple

class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail

class FastAPI:
    def __init__(self, *args, **kwargs):
        self.routes: Dict[Tuple[str, str], Callable] = {}
        self.middleware = []

    def add_middleware(self, middleware_class, **kwargs):
        self.middleware.append((middleware_class, kwargs))

    def get(self, path: str):
        def decorator(func: Callable):
            self.routes[("GET", path)] = func
            return func
        return decorator

    def post(self, path: str):
        def decorator(func: Callable):
            self.routes[("POST", path)] = func
            return func
        return decorator

class Response:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload
        try:
            self.text = json.dumps(payload)
        except TypeError:
            self.text = str(payload)

    def json(self):
        return self._payload
