from unittest.mock import AsyncMock

import httpx
import pytest

from app.common.exceptions import AppException
from app.research_providers.http_client import SafeResearchHttpClient


@pytest.mark.asyncio
async def test_fetches_allowed_html_with_bounded_client(monkeypatch):
    monkeypatch.setattr(SafeResearchHttpClient, "_resolve_public_address", AsyncMock(return_value="93.184.216.34"))
    def handler(request):
        assert request.url.host == "93.184.216.34"
        assert request.headers["host"] == "shop.example"
        assert request.extensions["sni_hostname"] == "shop.example"
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, text="<html>ok</html>")
    transport = httpx.MockTransport(handler)
    client = SafeResearchHttpClient(transport=transport)
    body, content_type = await client.get("https://shop.example/product/1", "https://shop.example")
    assert body == "<html>ok</html>"
    assert content_type == "text/html"


@pytest.mark.asyncio
async def test_rejects_cross_domain_redirect(monkeypatch):
    monkeypatch.setattr(SafeResearchHttpClient, "_resolve_public_address", AsyncMock(return_value="93.184.216.34"))
    transport = httpx.MockTransport(lambda request: httpx.Response(302, headers={"location": "https://attacker.example/item"}))
    client = SafeResearchHttpClient(transport=transport)
    with pytest.raises(AppException) as exc:
        await client.get("https://shop.example/product/1", "https://shop.example")
    assert exc.value.code == "SOURCE_DOMAIN_MISMATCH"


@pytest.mark.asyncio
async def test_rejects_oversized_response(monkeypatch):
    monkeypatch.setattr(SafeResearchHttpClient, "_resolve_public_address", AsyncMock(return_value="93.184.216.34"))
    transport = httpx.MockTransport(lambda request: httpx.Response(200, headers={"content-type": "application/json"}, content=b"x" * 11))
    client = SafeResearchHttpClient(max_bytes=10, transport=transport)
    with pytest.raises(AppException) as exc:
        await client.get("https://shop.example/product/1", "https://shop.example")
    assert exc.value.code == "SOURCE_RESPONSE_TOO_LARGE"
