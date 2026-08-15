from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import AppException
from app.services.brand_service import BrandService


@pytest.mark.asyncio
async def test_duplicate_brand_code_is_rejected():
    repository = SimpleNamespace(find_by_code=_async(SimpleNamespace(id=uuid4())))
    with pytest.raises(AppException) as error:
        await BrandService(repository).create({"brand_code": "gucci"})
    assert error.value.code == "DUPLICATE_BRAND_CODE"


@pytest.mark.asyncio
async def test_brand_in_use_must_be_deactivated_instead_of_deleted():
    brand = SimpleNamespace(id=uuid4())
    repository = SimpleNamespace(find_by_id=_async(brand), candidate_reference_count=_async(1))
    with pytest.raises(AppException) as error:
        await BrandService(repository).delete(brand.id)
    assert error.value.code == "BRAND_IN_USE"


def _async(value):
    async def inner(*args, **kwargs):
        return value
    return inner
