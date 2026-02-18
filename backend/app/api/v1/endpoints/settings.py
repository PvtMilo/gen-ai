import io
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError

from app.core.config import OVERLAYS_DIR, OVERLAY_ALLOWED_SIZES


router = APIRouter(prefix="/settings", tags=["settings"])


class OverlayUploadOut(BaseModel):
    overlay_url: str
    width: int
    height: int


@router.post("/overlay", response_model=OverlayUploadOut)
def upload_overlay(file: UploadFile = File(...)):
    original_name = file.filename or ""
    ext = Path(original_name).suffix.lower()
    content_type = (file.content_type or "").lower()

    if ext and ext != ".png":
        raise HTTPException(status_code=400, detail="Overlay must be .png")
    if content_type and content_type != "image/png":
        raise HTTPException(status_code=400, detail="Overlay content type must be image/png")

    raw = file.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        with Image.open(io.BytesIO(raw)) as img:
            img.load()
            if img.format != "PNG":
                raise HTTPException(status_code=400, detail="Overlay must be PNG format")
            width, height = img.size
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Invalid image file") from exc

    if (width, height) not in OVERLAY_ALLOWED_SIZES:
        raise HTTPException(
            status_code=400,
            detail="Overlay resolution must be 1200x1800 or 2400x3600",
        )

    OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    (OVERLAYS_DIR / filename).write_bytes(raw)

    return OverlayUploadOut(
        overlay_url=f"/static/overlays/{filename}",
        width=width,
        height=height,
    )
