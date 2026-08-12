from pathlib import Path
from uuid import UUID

from fastapi import status

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
        ingestion_service: DocumentIngestionService,
        document_repository: DocumentRepository,
    ):
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

        checksum = calculate_sha256(file_content)
        existing = await self.document_repository.find_by_checksum(
            checksum=checksum,
            knowledge_base_id=knowledge_base_id,
        )
        if existing is not None:
            raise DuplicateDocumentFileException()

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
        result = await self.ingestion_service.ingest(
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
                status="active",
                embedding_model_id=embedding_model_id,
                chunk_size=chunk_size,
                auto_enqueue=False,
            )
        )

        return {
            "filename": filename,
            "file_size": file_size,
            **result,
        }
