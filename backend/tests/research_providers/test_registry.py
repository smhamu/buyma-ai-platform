from types import SimpleNamespace

import pytest

from app.common.exceptions import AppException
from app.research_providers.registry import ResearchProviderRegistry


def test_registry_requires_explicit_supported_parser_key():
    provider = SimpleNamespace()
    registry = ResearchProviderRegistry({"supplier_product_v1": provider})
    assert registry.get("supplier_product_v1") is provider
    with pytest.raises(AppException) as exc:
        registry.get("unknown")
    assert exc.value.code == "RESEARCH_PROVIDER_NOT_CONFIGURED"
