from uuid import UUID

from app.common.exceptions import NotFoundException
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository


class DocumentChunkService:
    def __init__(
        self,
        chunk_repository: DocumentChunkRepository,
        document_repository: DocumentRepository,
    ):
        self.chunk_repository = chunk_repository
        self.document_repository = document_repository

    def split_text(self, text: str, chunk_size: int = 500) -> list[str]:
        return [
            text[i : i + chunk_size]
            for i in range(0, len(text), chunk_size)
            if text[i : i + chunk_size].strip()
        ]

    async def generate_chunks(self, document_id: UUID):
        document = await self.document_repository.find_by_id(document_id)

        if document is None:
            raise NotFoundException("Document")

        await self.chunk_repository.delete_by_document_id(document_id)

        chunks = self.split_text(document.content)

        created_chunks = []

        for index, content in enumerate(chunks):
            chunk = await self.chunk_repository.create(
                {
                    "document_id": document.id,
                    "chunk_index": index,
                    "content": content,
                }
            )
            created_chunks.append(chunk)

        return created_chunks

    async def list_chunks(self, document_id: UUID):
        document = await self.document_repository.find_by_id(document_id)

        if document is None:
            raise NotFoundException("Document")

        return await self.chunk_repository.find_by_document_id(document_id)