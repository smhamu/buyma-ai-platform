from uuid import UUID

from pydantic import BaseModel


class PromptBuildRequest(BaseModel):
    query: str
    embedding_model_id: UUID
    top_k: int = 5


class PromptMessage(BaseModel):
    role: str
    content: str


class PromptBuildResponse(BaseModel):
    query: str
    context: str
    messages: list[PromptMessage]
