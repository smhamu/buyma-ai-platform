from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.documents import router as documents_router
from app.api.v1.document_ingestion import router as document_ingestion_router
from app.api.v1.document_chunks import router as document_chunks_router
from app.common.exceptions import AppException
from app.core.logging import setup_logging, logger
from app.core.config import settings
from app.api.v1.embedding_models import router as embedding_models_router
from app.api.v1.embedding_providers import router as embedding_providers_router
from app.api.v1.embedding_jobs import router as embedding_jobs_router
from app.api.v1.embeddings import router as embeddings_router
from app.api.v1.vector_search import router as vector_search_router
from app.api.v1.retriever import router as retriever_router
from app.api.v1.prompt_builder import router as prompt_builder_router
from app.api.v1.rag import router as rag_router
from app.api.v1.knowledge_bases import router as knowledge_bases_router
from app.api.v1.document_versions import router as document_versions_router
from app.common.exception_handlers import validation_exception_handler


setup_logging()

app = FastAPI(
    title="BUYMA AI Platform API",
    description=(
        "Backend API for BUYMA AI Platform. "
        "Provides authentication, knowledge base management, "
        "document ingestion, embeddings, vector search and RAG."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_api_docs else None,
    openapi_url="/openapi.json" if settings.enable_api_docs else None,
)

cors_allowed_origins = [
    origin.strip()
    for origin in settings.cors_allowed_origins.split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(f"{exc.code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.exception("Unexpected error occurred")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error.",
        },
    )


@app.get("/health", tags=["Health"], summary="Health check")
def health_check():
    return {"status": "ok"}

@app.get("/env")
def get_env():
    return {
        "app_env": settings.app_env,
    }

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(knowledge_bases_router)
app.include_router(document_ingestion_router)
app.include_router(document_versions_router)
app.include_router(documents_router)
app.include_router(document_chunks_router)
app.include_router(embedding_providers_router)
app.include_router(embedding_models_router)
app.include_router(embedding_jobs_router)
app.include_router(embeddings_router)
app.include_router(vector_search_router)
app.include_router(retriever_router)
app.include_router(prompt_builder_router)
app.include_router(rag_router)
