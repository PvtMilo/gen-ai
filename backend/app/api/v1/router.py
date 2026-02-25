from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.sessions import router as sessions_router
from app.api.v1.endpoints.themes import router as themes_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.gallery import router as gallery_router
from app.api.v1.endpoints.drive import router as drive_router
from app.api.v1.endpoints.printer import router as printer_router
from app.api.v1.endpoints.settings import router as settings_router
from app.api.v1.endpoints.token_estimator import router as token_estimator_router
from app.api.v1.endpoints.event_maintenance import router as event_maintenance_router


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(sessions_router)
api_router.include_router(themes_router)
api_router.include_router(jobs_router)
api_router.include_router(gallery_router)
api_router.include_router(drive_router)
api_router.include_router(printer_router)
api_router.include_router(settings_router)
api_router.include_router(token_estimator_router)
api_router.include_router(event_maintenance_router)
