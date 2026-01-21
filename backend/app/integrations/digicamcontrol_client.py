# backend/services/digicam_control.py
from pathlib import Path
from typing import Optional

import requests

from app.core.config import (
    DIGICAM_BASE_URL,
    DIGICAM_CAPTURE_CMD,
    DIGICAM_PREVIEW_PATH,
)

__all__ = ["trigger_capture", "get_preview_image", "get_latest_file"]


def _build_url(path_or_query: str) -> str:
    """
    Gabungkan base URL digiCamControl dengan path atau query.
    Kalau sudah diawali http/https, kembalikan apa adanya.
    """
    if path_or_query.startswith(("http://", "https://")):
        return path_or_query
    return DIGICAM_BASE_URL.rstrip("/") + path_or_query


def trigger_capture() -> None:
    """Minta digiCamControl untuk jepret foto via webserver command /?CMD=Capture."""
    url = _build_url(DIGICAM_CAPTURE_CMD)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()


def get_preview_image() -> tuple[bytes, str]:
    """Ambil gambar dari digiCamControl (liveview/preview)."""
    url = _build_url(DIGICAM_PREVIEW_PATH)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "image/jpeg")
    return resp.content, content_type


def get_latest_file(directory: Path) -> Optional[Path]:
    """
    Ambil file terbaru (berdasarkan mtime) dari sebuah folder.
    Hanya mempertimbangkan file biasa, bukan folder.
    """
    if not directory.exists():
        return None

    files = [p for p in directory.iterdir() if p.is_file()]
    if not files:
        return None

    return max(files, key=lambda p: p.stat().st_mtime)
