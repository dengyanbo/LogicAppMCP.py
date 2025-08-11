import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_root_health(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("message")


def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"


def test_logic_apps_list_handles_empty(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Stub out client list calls to avoid Azure
    from app.main import consumption_client, standard_client

    async def fake_list_logic_apps():
        return []

    monkeypatch.setattr(consumption_client, "list_logic_apps", fake_list_logic_apps)
    monkeypatch.setattr(standard_client, "list_logic_apps", fake_list_logic_apps)

    resp = client.get("/logic-apps")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 0

