from fastapi import APIRouter
from app.api.v1.endpoints import health, ingest, search, models, sessions, chat, artifacts

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(ingest.router, tags=["Ingestion"])
api_router.include_router(search.router, tags=["Search"])
api_router.include_router(models.router)
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(artifacts.router, tags=["Artifacts"])

