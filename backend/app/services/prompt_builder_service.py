from app.schemas.prompt_builder import (
    PromptBuildRequest,
    PromptBuildResponse,
    PromptMessage,
)
from app.schemas.retriever import RetrieverRequest
from app.services.retriever_service import RetrieverService


class PromptBuilderService:
    def __init__(self, retriever_service: RetrieverService):
        self.retriever_service = retriever_service

    async def build(self, payload: PromptBuildRequest) -> PromptBuildResponse:
        retrieved = await self.retriever_service.retrieve(
            RetrieverRequest(
                query=payload.query,
                embedding_model_id=payload.embedding_model_id,
                top_k=payload.top_k,
            )
        )
        messages = self._build_messages(
            query=payload.query,
            context=retrieved.context,
        )

        return PromptBuildResponse(
            query=payload.query,
            context=retrieved.context,
            messages=messages,
            chunks=retrieved.chunks,
        )

    @staticmethod
    def _build_messages(query: str, context: str) -> list[PromptMessage]:
        system_prompt = (
            "あなたはBUYMA AI Platformのアシスタントです。\n"
            "以下のルールに従って回答してください。\n\n"
            "1. 提供されたContextを優先して回答すること。\n"
            "2. Contextに記載されていない内容を断定しないこと。\n"
            "3. Contextだけでは回答できない場合は、"
            "その旨を明確に伝えること。\n"
            "4. 回答は簡潔かつ分かりやすい日本語で記述すること。"
        )
        context_text = context or "関連するContextは取得できませんでした。"
        user_prompt = (
            "以下のContextを参考に質問へ回答してください。\n\n"
            f"## Context\n{context_text}\n\n"
            f"## Question\n{query}"
        )

        return [
            PromptMessage(role="system", content=system_prompt),
            PromptMessage(role="user", content=user_prompt),
        ]
