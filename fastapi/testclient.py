"""Simple TestClient stub to invoke FastAPI route handlers."""
import asyncio
from typing import Any
from . import Response, HTTPException

class TestClient:
    __test__ = False  # prevent pytest from collecting as tests
    def __init__(self, app):
        self.app = app

    def _run_handler(self, method: str, path: str, *args, **kwargs) -> Response:
        handler = self.app.routes.get((method, path))
        if handler is None:
            return Response(404, {"detail": "Not found"})
        try:
            result = handler(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = asyncio.get_event_loop().run_until_complete(result)
            return Response(200, result)
        except HTTPException as exc:  # pragma: no cover - preserves parity with FastAPI behavior
            return Response(exc.status_code, {"detail": exc.detail})

    def get(self, path: str, *args, **kwargs) -> Response:
        return self._run_handler("GET", path, *args, **kwargs)

    def post(self, path: str, *args, **kwargs) -> Response:
        return self._run_handler("POST", path, *args, **kwargs)
