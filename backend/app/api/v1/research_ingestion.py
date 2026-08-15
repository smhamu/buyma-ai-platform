from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.exceptions import AppException
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.brand_repository import BrandRepository
from app.repositories.product_research_repository import ProductResearchRepository
from app.repositories.research_ingestion_repository import ResearchIngestionRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.pagination import PaginatedResponse
from app.schemas.product_research import ProductResearchResponse
from app.schemas.research_ingestion import CandidateConversionRequest, CsvImportResponse, CsvRowResult, ResearchSourceResponse, UrlIngestionRequest
from app.services.research_ingestion_service import ResearchIngestionService
from app.repositories.product_category_repository import ProductCategoryRepository

router = APIRouter(prefix="/research-ingestion", tags=["Research Ingestion"])


def get_service(db: AsyncSession = Depends(get_db)):
    return ResearchIngestionService(ResearchIngestionRepository(db), SupplierRepository(db), BrandRepository(db), ProductResearchRepository(db), ProductCategoryRepository(db))


@router.post("/url")
async def register_url(payload: UrlIngestionRequest, service: ResearchIngestionService = Depends(get_service), user: User = Depends(get_current_user)):
    source = await service.register_url(payload.supplier_id, str(payload.url), user.id, user.role == "admin", payload.category_id)
    return success_response(data=ResearchSourceResponse.model_validate(source), message="Source URL registered. No external request was made.")


@router.post("/csv")
async def import_csv(file: UploadFile = File(...), service: ResearchIngestionService = Depends(get_service), user: User = Depends(get_current_user)):
    if not (file.filename or "").lower().endswith(".csv"): raise AppException(422, "INVALID_CSV", "A CSV file is required.")
    rows = await service.import_csv(await file.read(), user.id, user.role == "admin")
    data = CsvImportResponse(success_count=sum(x["status"] == "success" for x in rows), failed_count=sum(x["status"] == "failed" for x in rows), duplicate_count=sum(x["status"] == "duplicate" for x in rows), rows=[CsvRowResult(**x) for x in rows])
    return success_response(data=data, message="CSV import completed with row-level results.")


@router.get("")
async def list_sources(supplier_id: UUID | None = None, brand_id: UUID | None = None, source_type: str | None = None, processing_status: str | None = None, q: str | None = Query(None, max_length=500), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), service: ResearchIngestionService = Depends(get_service), user: User = Depends(get_current_user)):
    result = await service.repository.find_filtered(owner_id=None if user.role == "admin" else user.id, supplier_id=supplier_id, brand_id=brand_id, source_type=source_type, status=processing_status, q=q, page=page, page_size=page_size)
    data = PaginatedResponse[ResearchSourceResponse](items=[ResearchSourceResponse.model_validate(x) for x in result["items"]], page=page, page_size=page_size, total=result["total"], total_pages=(result["total"] + page_size - 1) // page_size)
    return success_response(data=data, message="Research sources fetched successfully.")


@router.get("/{source_id}")
async def get_source(source_id: UUID, service: ResearchIngestionService = Depends(get_service), user: User = Depends(get_current_user)):
    return success_response(data=ResearchSourceResponse.model_validate(await service.require_access(source_id, user.id, user.role == "admin")), message="Research source fetched successfully.")


@router.post("/{source_id}/create-candidate")
async def create_candidate(source_id: UUID, payload: CandidateConversionRequest, service: ResearchIngestionService = Depends(get_service), user: User = Depends(get_current_user)):
    source = await service.require_access(source_id, user.id, user.role == "admin")
    candidate = await service.create_candidate(source, payload, user.id, user.role == "admin")
    return success_response(data=ProductResearchResponse.model_validate(candidate), message="Candidate created from source.")


@router.delete("/{source_id}")
async def delete_source(source_id: UUID, service: ResearchIngestionService = Depends(get_service), user: User = Depends(get_current_user)):
    source = await service.require_access(source_id, user.id, user.role == "admin")
    if source.candidate_id: raise AppException(409, "SOURCE_IN_USE", "Converted source records cannot be deleted.")
    await service.repository.delete(source)
    return success_response(data={"deleted": True}, message="Research source deleted.")
