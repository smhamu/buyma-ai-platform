from types import SimpleNamespace

import pytest

from app.api.deps import require_admin
from app.common.exceptions import AppException


def test_admin_authorized_for_brand_mutation():
    user = SimpleNamespace(role="admin")
    assert require_admin(user) is user


def test_non_admin_forbidden_for_brand_mutation():
    with pytest.raises(AppException) as error:
        require_admin(SimpleNamespace(role="user"))
    assert error.value.code == "ADMIN_REQUIRED"
