from pathlib import Path
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AppException, DuplicateDocumentFileException
from app.document_extractors.factory import DocumentTextExtractorFactory
from app.repositories.document_repository import DocumentRepository
from app.schemas.document_ingestion import DocumentIngestionRequest
from app.services.document_ingestion_service import DocumentIngestionService
from app.utils.checksum import calculate_sha256


class DocumentFileIngestionService:
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(
        self,
        db: AsyncSession,
        ingestion_service: DocumentIngestionService,
        document_repository: DocumentRepository,
    ):
        self.db = db
        self.ingestion_service = ingestion_service
        self.document_repository = document_repository

    async def ingest_file(
        self,
        filename: str,
        file_content: bytes,
        embedding_model_id: UUID,
        mime_type: str | None = None,
        knowledge_base_id: UUID | None = None,
        chunk_size: int = 500,
    ):
        file_size = len(file_content)
        if file_size > self.MAX_FILE_SIZE:
            raise AppException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                code="DOCUMENT_FILE_TOO_LARGE",
                message="Document file exceeds the maximum allowed size.",
            )

        extension = Path(filename).suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise AppException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                code="UNSUPPORTED_DOCUMENT_FILE",
                message="Only PDF, TXT and Markdown files are supported.",
            )

        try:
            extractor = DocumentTextExtractorFactory.create(extension)
            content = extractor.extract(file_content).strip()
        except UnicodeDecodeError as exc:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="DOCUMENT_TEXT_EXTRACTION_FAILED",
                message="Failed to extract text from document file.",
            ) from exc
        except ValueError as exc:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="DOCUMENT_TEXT_EXTRACTION_FAILED",
                message="Failed to extract text from document file.",
            ) from exc

        if not content:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="DOCUMENT_TEXT_EXTRACTION_FAILED",
                message="Failed to extract text from document file.",
            )

        title = Path(filename).stem
        checksum = calculate_sha256(file_content)

        if self.db.in_transaction():
            try:
                result = await self._ingest_file_in_transaction(
                    filename=filename,
                    file_size=file_size,
                    content=content,
                    checksum=checksum,
                    title=title,
                    embedding_model_id=embedding_model_id,
                    mime_type=mime_type,
                    knowledge_base_id=knowledge_base_id,
                    chunk_size=chunk_size,
                )
                await self.db.commit()
            except Exception:
                await self.db.rollback()
                raise
        else:
            async with self.db.begin():
                result = await self._ingest_file_in_transaction(
                    filename=filename,
                    file_size=file_size,
                    content=content,
                    checksum=checksum,
                    title=title,
                    embedding_model_id=embedding_model_id,
                    mime_type=mime_type,
                    knowledge_base_id=knowledge_base_id,
                    chunk_size=chunk_size,
                )

        return {
            "filename": filename,
            "file_size": file_size,
            **result,
        }

    async def _ingest_file_in_transaction(
        self,
        *,
        filename: str,
        file_size: int,
        content: str,
        checksum: str,
        title: str,
        embedding_model_id: UUID,
        mime_type: str | None,
        knowledge_base_id: UUID | None,
        chunk_size: int,
    ):
        latest_document = await self.document_repository.find_latest_by_filename(
            knowledge_base_id=knowledge_base_id,
            original_filename=filename,
        )
        if latest_document is None:
            version = 1
            previous_document_id = None
            version_group_id = uuid4()
        else:
            if latest_document.checksum == checksum:
                raise DuplicateDocumentFileException()

            latest_document.is_latest = False
            await self.db.flush()

            version = latest_document.version + 1
            previous_document_id = latest_document.id
            version_group_id = latest_document.version_group_id

        result = await self.ingestion_service.ingest_in_transaction(
            DocumentIngestionRequest(
                knowledge_base_id=knowledge_base_id,
                title=title,
                content=content,
                source_type="file",
                source_url=None,
                original_filename=filename,
                mime_type=mime_type,
                file_size=file_size,
                checksum=checksum,
                version=version,
                previous_document_id=previous_document_id,
                version_group_id=version_group_id,
                is_latest=True,
                status="active",
                embedding_model_id=embedding_model_id,
                chunk_size=chunk_size,
                auto_enqueue=False,
            )
        )
        return result
