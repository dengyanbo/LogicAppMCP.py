import pytest

from app.consumption.client import ConsumptionLogicAppClient


@pytest.mark.asyncio
async def test_list_logic_apps_returns_list(monkeypatch: pytest.MonkeyPatch):
    client = ConsumptionLogicAppClient()

    class WF:
        def __init__(self, name):
            self.name = name
            self.id = name
            self.location = "eastus"
            self.state = "Enabled"
            self.created_time = None
            self.changed_time = None

    # Replace internal list call to avoid Azure
    async def fake_list_sync(func, *args, **kwargs):
        return [WF("a"), WF("b")]

    monkeypatch.setattr(client, "_list_sync", fake_list_sync)

    items = await client.list_logic_apps()
    assert isinstance(items, list)
    assert len(items) == 2

