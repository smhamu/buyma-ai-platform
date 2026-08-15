from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.models.brand import Brand
from scripts.seed_prada_eu_suppliers import CONSERVATIVE_POLICY, PRADA_EU_SUPPLIERS, seed_prada_eu_suppliers


def make_session(*, brand, existing=()):
    return SimpleNamespace(scalar=AsyncMock(return_value=brand), scalars=AsyncMock(return_value=SimpleNamespace(all=lambda: list(existing))), add_all=Mock(), commit=AsyncMock())


def test_seed_has_four_unique_eur_country_suppliers():
    assert {item["country_code"] for item in PRADA_EU_SUPPLIERS} == {"FR", "DE", "IT", "ES"}
    assert len({item["name"] for item in PRADA_EU_SUPPLIERS}) == 4
    assert len({item["website_url"] for item in PRADA_EU_SUPPLIERS}) == 4
    assert CONSERVATIVE_POLICY["default_currency"] == "EUR"


def test_seed_policy_is_conservative():
    assert CONSERVATIVE_POLICY["ships_to_japan"] is False
    assert CONSERVATIVE_POLICY["vat_policy"] == "not_refunded"
    assert CONSERVATIVE_POLICY["buyma_allowed_status"] == "unchecked"
    assert CONSERVATIVE_POLICY["ingestion_source_type"] == "url_manual"
    assert CONSERVATIVE_POLICY["automated_fetch_enabled"] is False
    assert CONSERVATIVE_POLICY["terms_status"] == "restricted"
    assert CONSERVATIVE_POLICY["robots_status"] == "restricted"
    assert CONSERVATIVE_POLICY["official_api_available"] is False


@pytest.mark.asyncio
async def test_seed_relates_new_suppliers_to_prada_brand():
    brand = Brand(id=uuid4(), brand_code="prada", brand_name="Prada", luxury_tier="luxury", online_purchase_policy="unknown", is_research_enabled=True, is_active=True)
    session = make_session(brand=brand)
    assert await seed_prada_eu_suppliers(session, uuid4()) == 4
    assert all(supplier.brands == [brand] for supplier in session.add_all.call_args.args[0])
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_seed_does_not_overwrite_existing_suppliers():
    existing = [SimpleNamespace(name=item["name"]) for item in PRADA_EU_SUPPLIERS]
    session = make_session(brand=SimpleNamespace(id=uuid4()), existing=existing)
    assert await seed_prada_eu_suppliers(session, uuid4()) == 0
    session.add_all.assert_not_called()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_seed_fails_closed_when_prada_brand_is_missing():
    session = make_session(brand=None)
    with pytest.raises(RuntimeError, match="Prada brand is missing"):
        await seed_prada_eu_suppliers(session, uuid4())
    session.scalars.assert_not_awaited()
    session.add_all.assert_not_called()
