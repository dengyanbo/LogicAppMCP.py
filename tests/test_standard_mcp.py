import json
import pytest

from app.standard.mcp_handler import StandardMCPHandler


@pytest.mark.asyncio
async def test_initialize_returns_capabilities():
    handler = StandardMCPHandler()
    req = {"id": 2, "method": "initialize", "params": {}}
    res = await handler.handle_request(req)
    assert res.get("id") == 2
    assert res["result"]["protocolVersion"] == "2024-11-05"


@pytest.mark.asyncio
async def test_tools_list_and_call_validation(monkeypatch: pytest.MonkeyPatch):
    handler = StandardMCPHandler()
    res = await handler.handle_request({"method": "tools/list"})
    assert "tools" in res["result"]

    # missing required
    res2 = await handler.handle_request({"method": "tools/call", "params": {"name": "get_standard_logic_app", "arguments": {}}})
    assert "error" in res2 and res2["error"]["code"] == -32602

    # stub client
    async def fake_get_logic_app(name: str):
        return {"name": name, "plan_type": "standard"}

    monkeypatch.setattr(handler.logicapp_client, "get_logic_app", fake_get_logic_app)
    ok = await handler.handle_request({"method": "tools/call", "params": {"name": "get_standard_logic_app", "arguments": {"workflow_name": "wf2"}}})
    payload = ok["result"]["content"][0]["text"]
    data = json.loads(payload)
    assert data["plan_type"] == "standard"

