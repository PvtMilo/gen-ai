from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.sessions import router as sessions_router
from app.api.v1.endpoints.themes import router as themes_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.gallery import router as gallery_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(sessions_router)
api_router.include_router(themes_router)
api_router.include_router(jobs_router)
api_router.include_router(gallery_router)
