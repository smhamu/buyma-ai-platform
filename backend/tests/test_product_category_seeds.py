from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from scripts.seed_chanel_category_policies import CHANEL_POLICIES, seed_chanel_category_policies
from scripts.seed_product_categories import PRODUCT_CATEGORIES, seed_product_categories


@pytest.mark.asyncio
async def test_category_seed_is_complete_and_idempotent():
    session = SimpleNamespace(scalars=AsyncMock(return_value=SimpleNamespace(all=lambda: [])), add_all=Mock(), commit=AsyncMock())
    assert len(PRODUCT_CATEGORIES) == 10
    assert await seed_product_categories(session) == 10
    session.add_all.assert_called_once()


@pytest.mark.asyncio
async def test_category_seed_does_not_overwrite_existing():
    codes = [code for code, _ in PRODUCT_CATEGORIES]
    session = SimpleNamespace(scalars=AsyncMock(return_value=SimpleNamespace(all=lambda: codes)), add_all=Mock(), commit=AsyncMock())
    assert await seed_product_categories(session) == 0
    session.add_all.assert_not_called()


@pytest.mark.asyncio
async def test_chanel_seed_creates_only_evidenced_overrides():
    brand = SimpleNamespace(id=uuid4())
    categories = [SimpleNamespace(id=uuid4(), category_code=code) for code in CHANEL_POLICIES]
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=brand),
        scalars=AsyncMock(side_effect=[SimpleNamespace(all=lambda: categories), SimpleNamespace(all=lambda: [])]),
        add_all=Mock(), commit=AsyncMock(),
    )
    assert await seed_chanel_category_policies(session) == 6
    values = session.add_all.call_args.args[0]
    assert {x.online_purchase_policy for x in values} == {"normal", "boutique_only"}


@pytest.mark.asyncio
async def test_chanel_seed_fails_closed_without_brand():
    session = SimpleNamespace(scalar=AsyncMock(return_value=None), add_all=Mock())
    with pytest.raises(RuntimeError, match="CHANEL brand is missing"):
        await seed_chanel_category_policies(session)
