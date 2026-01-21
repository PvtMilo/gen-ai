from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.db.session import engine
from app.db.base import Base
from app.core.config import UPLOADS_DIR, RESULTS_DIR, DATA_DIR

# IMPORTANT: pastikan model ter-import sebelum create_all
from app.modules.users.model import User  # noqa: F401
from app.modules.sessions.model import PhotoSession  # noqa: F401
# nanti tambah Job dll kalau sudah

def ensure_dirs():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Generative API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # default Vite
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# static mount
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def on_startup():
    ensure_dirs()
    # DEV ONLY: create tables otomatis (nanti kalau sudah serius pindah ke Alembic)
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/health")
def health():
    return {"ok": True}
