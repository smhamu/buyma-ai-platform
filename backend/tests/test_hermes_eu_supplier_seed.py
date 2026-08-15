from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from scripts.seed_hermes_eu_suppliers import (
    CONSERVATIVE_POLICY,
    HERMES_EU_SUPPLIERS,
    seed_hermes_eu_suppliers,
)


def test_seed_has_four_unique_country_suppliers():
    assert {item["country_code"] for item in HERMES_EU_SUPPLIERS} == {
        "FR",
        "DE",
        "IT",
        "ES",
    }
    assert len({item["name"] for item in HERMES_EU_SUPPLIERS}) == 4
    assert len({item["website_url"] for item in HERMES_EU_SUPPLIERS}) == 4


def test_seed_policy_is_manual_and_fail_closed():
    assert CONSERVATIVE_POLICY["default_currency"] == "EUR"
    assert CONSERVATIVE_POLICY["ships_to_japan"] is False
    assert CONSERVATIVE_POLICY["vat_policy"] == "not_refunded"
    assert CONSERVATIVE_POLICY["ingestion_source_type"] == "url_manual"
    assert CONSERVATIVE_POLICY["automated_fetch_enabled"] is False
    assert CONSERVATIVE_POLICY["terms_status"] == "restricted"
    assert CONSERVATIVE_POLICY["official_api_available"] is False
    assert CONSERVATIVE_POLICY["parser_key"] is None


@pytest.mark.asyncio
async def test_seed_does_not_update_or_recreate_existing_suppliers():
    existing = [SimpleNamespace(name=item["name"]) for item in HERMES_EU_SUPPLIERS]
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=SimpleNamespace(id=uuid4())),
        scalars=AsyncMock(return_value=SimpleNamespace(all=lambda: existing)),
        add_all=Mock(),
        commit=AsyncMock(),
    )

    created = await seed_hermes_eu_suppliers(session, uuid4())

    assert created == 0
    session.add_all.assert_not_called()
    session.commit.assert_not_awaited()
