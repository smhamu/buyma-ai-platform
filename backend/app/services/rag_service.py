from app.ai.chat.factory import ChatProviderFactory
from app.core.config import settings
from app.schemas.prompt_builder import PromptBuildRequest
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGSource
from app.services.prompt_builder_service import PromptBuilderService


class RAGService:
    def __init__(self, prompt_builder_service: PromptBuilderService):
        self.prompt_builder_service = prompt_builder_service

    async def query(self, payload: RAGQueryRequest) -> RAGQueryResponse:
        prompt_result = await self.prompt_builder_service.build(
            PromptBuildRequest(
                query=payload.query,
                embedding_model_id=payload.embedding_model_id,
                knowledge_base_id=payload.knowledge_base_id,
                top_k=payload.top_k,
                distance_threshold=payload.distance_threshold,
            )
        )

        if not prompt_result.chunks:
            return RAGQueryResponse(
                query=payload.query,
                answer=(
                    "関連する情報が見つかりませんでした。"
                    "登録済みのDocumentに質問へ回答できる情報があるか確認してください。"
                ),
                context="",
                sources=[],
            )

        if not settings.openai_chat_model:
            raise ValueError("OPENAI_CHAT_MODEL is not configured.")

        chat_provider = ChatProviderFactory.create(
            provider_code="openai",
            model_name=settings.openai_chat_model,
        )
        messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in prompt_result.messages
        ]
        answer = await chat_provider.generate(messages=messages)
        sources = [
            RAGSource(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                distance=chunk.distance,
            )
            for chunk in prompt_result.chunks
        ]

        return RAGQueryResponse(
            query=payload.query,
            answer=answer,
            context=prompt_result.context,
            sources=sources,
        )
