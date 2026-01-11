# app/core/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = APP_DIR.parent

STATIC_DIR = APP_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
RESULTS_DIR = STATIC_DIR / "results"

THEMES_DIR = APP_DIR / "modules" / "themes" / "data"
THEMES_JSON = THEMES_DIR / "themes.json"

DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "app.db"

DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DB_PATH.as_posix()}"

class Settings:
    DATABASE_URL: str = DATABASE_URL

settings = Settings()
