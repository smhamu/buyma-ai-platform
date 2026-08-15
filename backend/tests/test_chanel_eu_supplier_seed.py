from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.models.brand import Brand
from scripts.seed_chanel_eu_suppliers import (
    CHANEL_EU_SUPPLIERS,
    CONSERVATIVE_POLICY,
    seed_chanel_eu_suppliers,
)


def make_session(*, brand, existing=()):
    return SimpleNamespace(
        scalar=AsyncMock(return_value=brand),
        scalars=AsyncMock(
            return_value=SimpleNamespace(all=lambda: list(existing))
        ),
        add_all=Mock(),
        commit=AsyncMock(),
    )


def test_seed_has_four_unique_country_suppliers():
    assert {item["country_code"] for item in CHANEL_EU_SUPPLIERS} == {
        "FR",
        "DE",
        "IT",
        "ES",
    }
    assert len({item["name"] for item in CHANEL_EU_SUPPLIERS}) == 4
    assert len({item["website_url"] for item in CHANEL_EU_SUPPLIERS}) == 4


def test_seed_policy_is_conservative():
    assert CONSERVATIVE_POLICY["default_currency"] == "EUR"
    assert CONSERVATIVE_POLICY["ships_to_japan"] is False
    assert CONSERVATIVE_POLICY["ingestion_source_type"] == "url_manual"
    assert CONSERVATIVE_POLICY["automated_fetch_enabled"] is False
    assert CONSERVATIVE_POLICY["terms_status"] == "restricted"
    assert CONSERVATIVE_POLICY["robots_status"] == "restricted"
    assert CONSERVATIVE_POLICY["official_api_available"] is False
    assert CONSERVATIVE_POLICY["parser_key"] is None
    assert {item["vat_policy"] for item in CHANEL_EU_SUPPLIERS} <= {
        "included",
        "unknown",
    }


@pytest.mark.asyncio
async def test_seed_relates_new_suppliers_to_chanel_brand():
    brand = Brand(
        id=uuid4(),
        brand_code="chanel",
        brand_name="CHANEL",
        luxury_tier="ultra_luxury",
        online_purchase_policy="research_only",
        is_research_enabled=True,
        is_active=True,
    )
    session = make_session(brand=brand)

    created = await seed_chanel_eu_suppliers(session, uuid4())

    assert created == 4
    suppliers = session.add_all.call_args.args[0]
    assert len(suppliers) == 4
    assert all(supplier.brands == [brand] for supplier in suppliers)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_seed_does_not_update_or_recreate_existing_suppliers():
    existing = [SimpleNamespace(name=item["name"]) for item in CHANEL_EU_SUPPLIERS]
    session = make_session(brand=SimpleNamespace(id=uuid4()), existing=existing)

    created = await seed_chanel_eu_suppliers(session, uuid4())

    assert created == 0
    session.add_all.assert_not_called()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_seed_fails_closed_when_chanel_brand_is_missing():
    session = make_session(brand=None)

    with pytest.raises(RuntimeError, match="CHANEL brand is missing"):
        await seed_chanel_eu_suppliers(session, uuid4())

    session.scalars.assert_not_awaited()
    session.add_all.assert_not_called()
    session.commit.assert_not_awaited()
