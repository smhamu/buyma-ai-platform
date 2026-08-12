import os

import pytest
from httpx import AsyncClient

from tests.evaluation.cases import RETRIEVAL_EVALUATION_CASES


EMBEDDING_MODEL_ID = os.getenv("TEST_EMBEDDING_MODEL_ID")


@pytest.mark.evaluation
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    RETRIEVAL_EVALUATION_CASES,
)
async def test_vector_search_retrieval_quality(case: dict[str, str]):
    if not EMBEDDING_MODEL_ID:
        pytest.skip("TEST_EMBEDDING_MODEL_ID is not configured.")

    async with AsyncClient(base_url="http://localhost:8000") as client:
        pytest.skip(
            "Authentication setup is required for integration evaluation."
        )
