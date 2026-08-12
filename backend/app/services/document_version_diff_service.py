from difflib import ndiff
from uuid import UUID

from fastapi import status

from app.common.exceptions import AppException, NotFoundException
from app.repositories.document_repository import DocumentRepository
from app.schemas.document_version_diff import (
    DocumentVersionDiffLine,
    DocumentVersionDiffResponse,
)


class DocumentVersionDiffService:
    def __init__(
        self,
        document_repository: DocumentRepository,
    ):
        self.document_repository = document_repository

    async def compare(
        self,
        base_document_id: UUID,
        compare_document_id: UUID,
    ) -> DocumentVersionDiffResponse:
        base_document = await self.document_repository.find_by_id(base_document_id)
        if base_document is None:
            raise NotFoundException("Document")

        compare_document = await self.document_repository.find_by_id(compare_document_id)
        if compare_document is None:
            raise NotFoundException("Document")

        if base_document.version_group_id != compare_document.version_group_id:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="DOCUMENT_VERSION_GROUP_MISMATCH",
                message="Documents belong to different version groups.",
            )

        added_count = 0
        removed_count = 0
        unchanged_count = 0
        lines: list[DocumentVersionDiffLine] = []

        for line in ndiff(
            base_document.content.splitlines(),
            compare_document.content.splitlines(),
        ):
            prefix = line[:2]
            content = line[2:]
            if prefix == "+ ":
                added_count += 1
                lines.append(DocumentVersionDiffLine(type="added", content=content))
            elif prefix == "- ":
                removed_count += 1
                lines.append(DocumentVersionDiffLine(type="removed", content=content))
            elif prefix == "  ":
                unchanged_count += 1
                lines.append(DocumentVersionDiffLine(type="unchanged", content=content))

        return DocumentVersionDiffResponse(
            base_document_id=base_document.id,
            base_version=base_document.version,
            compare_document_id=compare_document.id,
            compare_version=compare_document.version,
            lines=lines,
            added_count=added_count,
            removed_count=removed_count,
            unchanged_count=unchanged_count,
            has_changes=added_count > 0 or removed_count > 0,
        )
