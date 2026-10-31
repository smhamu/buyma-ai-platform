from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.deps import require_admin
from app.main import app
from app.notifications.secret_store import (
    InMemoryNotificationSecretStore,
    get_notification_secret_store,
    rakuten_product_search_token_reference,
)


def test_admin_can_manage_token_without_api_disclosure():
    store = InMemoryNotificationSecretStore()
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(role="admin")
    app.dependency_overrides[get_notification_secret_store] = lambda: store
    client = TestClient(app)
    token = "private-rakuten-token"
    try:
        response = client.get("/integration-settings/rakuten")
        assert response.status_code == 200
        assert response.json()["data"] == {"provider": "rakuten_product_search", "configured": False}

        response = client.put("/integration-settings/rakuten", json={"token": token})
        assert response.status_code == 200
        assert response.json()["data"]["configured"] is True
        assert token not in response.text

        response = client.get("/integration-settings/rakuten")
        assert response.json()["data"]["configured"] is True
        assert token not in response.text

        response = client.delete("/integration-settings/rakuten")
        assert response.status_code == 200
        assert response.json()["data"]["configured"] is False
    finally:
        app.dependency_overrides.clear()


def test_token_validation_rejects_whitespace_without_storing_secret():
    store = InMemoryNotificationSecretStore()
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(role="admin")
    app.dependency_overrides[get_notification_secret_store] = lambda: store
    client = TestClient(app)
    try:
        response = client.put("/integration-settings/rakuten", json={"token": " token\n"})
        assert response.status_code == 422
        assert not client.get("/integration-settings/rakuten").json()["data"]["configured"]
    finally:
        app.dependency_overrides.clear()


def test_rakuten_reference_is_environment_scoped():
    assert rakuten_product_search_token_reference("test") == (
        "/buyma-ai/test/integrations/rakuten/product-search-token"
    )
