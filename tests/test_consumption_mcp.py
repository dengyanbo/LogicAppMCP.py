import json
import pytest

from app.consumption.mcp_handler import ConsumptionMCPHandler


@pytest.mark.asyncio
async def test_initialize_returns_capabilities():
    handler = ConsumptionMCPHandler()
    req = {"id": 1, "method": "initialize", "params": {}}
    res = await handler.handle_request(req)
    assert res.get("id") == 1
    assert res["result"]["protocolVersion"] == "2024-11-05"


@pytest.mark.asyncio
async def test_tools_list_and_call_validation(monkeypatch: pytest.MonkeyPatch):
    handler = ConsumptionMCPHandler()
    # ensure list available
    res = await handler.handle_request({"method": "tools/list"})
    assert "tools" in res["result"]

    # validate required params error
    call = {
        "method": "tools/call",
        "params": {
            "name": "get_consumption_logic_app",
            "arguments": {
                "azure_context": {
                    "subscription_id": "sub",
                    "resource_group": "rg",
                    "tenant_id": "tenant",
                    "client_id": "client",
                    "client_secret": "secret",
                }
            },
        },
    }
    res2 = await handler.handle_request(call)
    assert "error" in res2 and res2["error"]["code"] == -32602

    # monkeypatch client to avoid azure
    async def fake_get_logic_app(name: str):
        return {"name": name, "id": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Logic/workflows/z"}

    monkeypatch.setattr(handler.logicapp_client, "get_logic_app", fake_get_logic_app)
    good_call = {
        "method": "tools/call",
        "params": {
            "name": "get_consumption_logic_app",
            "arguments": {
                "workflow_name": "wf1",
                "azure_context": {
                    "subscription_id": "sub",
                    "resource_group": "rg",
                    "tenant_id": "tenant",
                    "client_id": "client",
                    "client_secret": "secret",
                },
            },
        },
    }
    ok = await handler.handle_request(good_call)
    # result content is json text; ensure it decodes
    payload = ok["result"]["content"][0]["text"]
    data = json.loads(payload)
    assert data["name"] == "wf1"


@pytest.mark.asyncio
async def test_tools_list_includes_azure_context():
    handler = ConsumptionMCPHandler()
    res = await handler.handle_request({"method": "tools/list"})
    tools = res["result"]["tools"]

    for tool in tools:
        props = tool.get("inputSchema", {}).get("properties", {})
        assert "azure_context" in props or "azure" in props
        azure_context = props.get("azure_context") or props.get("azure")
        assert azure_context.get("type") == "object"
        azure_props = azure_context.get("properties", {})
        for expected in {"subscription_id", "resource_group", "tenant_id", "client_id", "client_secret"}:
            assert expected in azure_props

