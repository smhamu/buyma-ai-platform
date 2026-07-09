from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.documents import router as documents_router
from app.api.v1.document_chunks import router as document_chunks_router
from app.common.exceptions import AppException
from app.core.logging import setup_logging, logger
from app.core.config import settings
from app.api.v1.embedding_models import router as embedding_models_router
from app.api.v1.embedding_providers import router as embedding_providers_router
from app.api.v1.embedding_jobs import router as embedding_jobs_router
from app.api.v1.embeddings import router as embeddings_router


setup_logging()

app = FastAPI(
    title="BUYMA AI Platform",
    version="0.1.0",
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(f"{exc.code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
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


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/env")
def get_env():
    return {
        "app_env": settings.app_env,
    }

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(documents_router)
app.include_router(document_chunks_router)
app.include_router(embedding_providers_router)
app.include_router(embedding_models_router)
app.include_router(embedding_jobs_router)
app.include_router(embeddings_router)
