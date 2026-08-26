from fastapi import APIRouter
from app.api.v1.endpoints import health, ingest, search

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(ingest.router, tags=["Ingestion"])
api_router.include_router(search.router, tags=["Search"])
