# app/core/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = APP_DIR.parent

STATIC_DIR = APP_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
CAPTURED_DIR = STATIC_DIR / "captured"
OVERLAYS_DIR = STATIC_DIR / "overlays"
# Folder asli tempat digiCamControl menyimpan foto dari kamera
# Default diset ke path yang kamu berikan, tapi bisa dioverride pakai env DIGICAM_ORIGINAL_DIR
DIGICAM_ORIGINAL_DIR = Path(
    os.getenv(
        "DIGICAM_ORIGINAL_DIR",
        r"C:\Users\flip3\Pictures\digiCamControl\test samuel",
    )
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
# Konfigurasi digiCamControl webserver
# Default: http://127.0.0.1:5513
DIGICAM_BASE_URL = os.getenv("DIGICAM_BASE_URL", "http://127.0.0.1:5513")
# Path untuk live view di digiCamControl webserver
# Kita pakai /liveview.jpg untuk preview/live view
DIGICAM_PREVIEW_PATH = os.getenv("DIGICAM_PREVIEW_PATH", "/liveview.jpg")
DIGICAM_CAPTURE_CMD = os.getenv("DIGICAM_CAPTURE_CMD", "/?CMD=Capture")

RESULTS_DIR = STATIC_DIR / "results"
OVERLAY_ALLOWED_SIZES = {(1200, 1800), (2400, 3600)}

THEMES_DIR = APP_DIR / "modules" / "themes" / "data"
THEMES_JSON = THEMES_DIR / "themes.json"

DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "app.db"

DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DB_PATH.as_posix()}"


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")


SEEDDREAM_SIZE = os.getenv("SEEDDREAM_SIZE", "2400x3600")
SEEDDREAM_WATERMARK = _env_bool("SEEDDREAM_WATERMARK", True)

class Settings:
    DATABASE_URL: str = DATABASE_URL

settings = Settings()
