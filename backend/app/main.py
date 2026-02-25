from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.api.v1.endpoints.camera import router as camera_router
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.db.ensure import (
    ensure_job_drive_columns,
    ensure_photo_sessions_theme_index,
    ensure_themes_serial_id,
)
from app.core.config import (
    UPLOADS_DIR,
    RESULTS_DIR,
    DATA_DIR,
    OVERLAYS_DIR,
    THUMBS_DIR,
    COMPRESSED_DIR,
)
from app.modules.themes.service import seed_themes_if_empty

from app.modules.users.model import User  # noqa: F401
from app.modules.sessions.model import PhotoSession  # noqa: F401
from app.modules.themes.model import Theme  # noqa: F401
from contextlib import asynccontextmanager


def ensure_dirs():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    COMPRESSED_DIR.mkdir(parents=True, exist_ok=True)
    OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    Base.metadata.create_all(bind=engine)
    ensure_job_drive_columns(engine)
    ensure_photo_sessions_theme_index(engine)
    ensure_themes_serial_id(engine)

    db = SessionLocal()
    try:
        seed_themes_if_empty(db)
    finally:
        db.close()

    yield  

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(camera_router)

# static mount
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/health")
def health():
    return {"ok": True}
