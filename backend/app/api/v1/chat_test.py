from fastapi import APIRouter, Depends

from app.ai.chat.factory import ChatProviderFactory
from app.api.deps import get_current_user
from app.common.responses import success_response
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/chat-test", tags=["Chat Test"])


@router.post("")
async def chat_test(
    current_user: User = Depends(get_current_user),
):
    if not settings.openai_chat_model:
        raise ValueError("OPENAI_CHAT_MODEL is not configured.")

    provider = ChatProviderFactory.create(
        provider_code="openai",
        model_name=settings.openai_chat_model,
    )
    answer = await provider.generate(
        messages=[
            {
                "role": "system",
                "content": "あなたはBUYMA AI Platformのアシスタントです。",
            },
            {
                "role": "user",
                "content": "こんにちは。",
            },
        ]
    )

    return success_response(
        data={"answer": answer},
        message="Chat generation completed successfully.",
    )
