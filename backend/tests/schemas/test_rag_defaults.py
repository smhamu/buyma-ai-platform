from uuid import uuid4

from app.schemas.prompt_builder import PromptBuildRequest
from app.schemas.rag import RAGQueryRequest
from app.schemas.retriever import RetrieverRequest
from app.schemas.vector_search import VectorSearchRequest


def test_vector_search_default_distance_threshold():
    request = VectorSearchRequest(
        query="test",
        embedding_model_id=uuid4(),
    )

    assert request.top_k == 5
    assert request.distance_threshold == 0.5


def test_retriever_default_distance_threshold():
    request = RetrieverRequest(
        query="test",
        embedding_model_id=uuid4(),
    )

    assert request.distance_threshold == 0.5


def test_prompt_builder_default_distance_threshold():
    request = PromptBuildRequest(
        query="test",
        embedding_model_id=uuid4(),
    )

    assert request.distance_threshold == 0.5


def test_rag_default_distance_threshold():
    request = RAGQueryRequest(
        query="test",
        embedding_model_id=uuid4(),
    )

    assert request.distance_threshold == 0.5
