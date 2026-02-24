import io
import os
import logging
from pathlib import Path

import qrcode
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import RESULTS_DIR
from app.db.session import get_db
from app.integrations.gdrive.client import get_credentials_status
from app.integrations.gdrive.service import upload_file_to_drive
from app.modules.jobs.service import sync_drive_links, upload_drive_link_for_job

router = APIRouter(prefix="/drive", tags=["drive"])
logger = logging.getLogger(__name__)


class DriveStatusOut(BaseModel):
    ok: bool
    status: str
    message: str
    expiry: str | None = None
    has_refresh_token: bool = False
    refreshed: bool = False
    checked_at: str


class DriveJobUploadOut(BaseModel):
    job_id: int
    result_url: str | None = None
    drive_link: str | None = None
    download_link: str | None = None
    qr_url: str | None = None
    uploaded: bool = False
    message: str = "uploaded"


@router.post("/sync")
def sync_drive(
    limit: int | None = None,
    force: bool = False,
    db: Session = Depends(get_db),
):
    try:
        return sync_drive_links(db, limit=limit, force=force)
    except RuntimeError as e:
        raise HTTPException(500, str(e))


@router.get("/status", response_model=DriveStatusOut)
def drive_status():
    status = get_credentials_status()
    logger.info(
        "drive_status checked: ok=%s status=%s expiry=%s",
        status.get("ok"),
        status.get("status"),
        status.get("expiry"),
    )
    return status


@router.post("/upload-job/{job_id}", response_model=DriveJobUploadOut)
def upload_job(job_id: int, force: bool = False, db: Session = Depends(get_db)):
    try:
        return upload_drive_link_for_job(db, job_id=job_id, force=force)
    except ValueError as e:
        msg = str(e)
        if msg == "JOB_NOT_FOUND":
            raise HTTPException(404, "Job not found")
        if msg == "RESULT_NOT_FOUND":
            raise HTTPException(400, "Job has no result image")
        if msg == "RESULT_FILE_NOT_FOUND":
            raise HTTPException(404, "Result file not found")
        raise
    except RuntimeError as e:
        raise HTTPException(500, str(e))


@router.post("/upload")
def upload_single(file: UploadFile = File(...)):
    try:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename or "").suffix
        temp_name = f"upload_{os.getpid()}_{id(file)}{suffix}"
        temp_path = RESULTS_DIR / temp_name

        with temp_path.open("wb") as f:
            f.write(file.file.read())

        uploaded = upload_file_to_drive(temp_path)
        return uploaded
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        try:
            if "temp_path" in locals() and temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


@router.get("/qr")
def generate_qr(url: str, size: int = 360):
    if not url:
        raise HTTPException(400, "url is required")

    size = max(120, min(int(size), 1024))

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
