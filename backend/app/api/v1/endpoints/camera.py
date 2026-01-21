# backend/api/camera.py
import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import API_BASE_URL
from app.integrations.digicamcontrol_client import get_preview_image
from app.modules.cameras.schema import CaptureResponse
from app.modules.cameras.service import capture_and_save_photo

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.get("/liveview")
def liveview():
    """
    Endpoint untuk live view (polling).
    Frontend akan memanggil ini berkala dan menampilkan sebagai <img>.
    """
    try:
        image_bytes, content_type = get_preview_image()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to get live view: {exc}") from exc

    return StreamingResponse(
        io.BytesIO(image_bytes),
        media_type=content_type,
    )


@router.get("/preview")
def preview():
    """
    Endpoint untuk melihat snapshot liveview (kalau mau dipakai).
    Untuk sekarang sama dengan liveview.
    """
    try:
        image_bytes, content_type = get_preview_image()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to get preview: {exc}") from exc

    return StreamingResponse(
        io.BytesIO(image_bytes),
        media_type=content_type,
    )


@router.post("/capture", response_model=CaptureResponse)
def capture():
    """
    Trigger kamera jepret via digiCamControl, lalu:
    - Cari file terbaru di folder asli digiCamControl
    - Copy ke backend/static/captured/
    - Kembalikan URL ke file static tersebut
    """
    try:
        filename = capture_and_save_photo()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to capture and save photo: {exc}") from exc

    # Bangun URL absolute ke static file
    # Contoh: http://localhost:8000/static/captured/20251202-134500_XXX.jpg
    photo_url = f"{API_BASE_URL.rstrip('/')}/static/captured/{filename}"

    return CaptureResponse(photo_url=photo_url)
