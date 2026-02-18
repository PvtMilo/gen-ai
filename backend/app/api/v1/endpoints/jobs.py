from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.jobs.schema import JobCreateIn, JobOut
from app.modules.jobs.service import create_job, process_job_seeddream_safe
from app.modules.jobs.model import Job

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", response_model=JobOut)
def create_job_endpoint(
    payload: JobCreateIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        job = create_job(
            db,
            payload.session_id,
            mode=payload.mode,
            overlay_url=payload.overlay_url,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "SESSION_NOT_FOUND":
            raise HTTPException(404, "Session not found")
        if msg == "THEME_NOT_SET":
            raise HTTPException(400, "Theme not set")
        if msg == "PHOTO_NOT_UPLOADED":
            raise HTTPException(400, "Photo not uploaded")
        if msg == "OVERLAY_INVALID":
            raise HTTPException(400, "Overlay path is invalid")
        if msg == "OVERLAY_NOT_FOUND":
            raise HTTPException(404, "Overlay not found")
        raise

    background.add_task(process_job_seeddream_safe, job.id, payload.mode)

    return JobOut(
        job_id=job.id,
        session_id=job.session_id,
        status=job.status,
        mode=job.mode or "event",
        overlay_url=job.overlay_image_path,
    )

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    return JobOut(
        job_id=job.id,
        session_id=job.session_id,
        status=job.status,
        mode=job.mode or "event",
        overlay_url=job.overlay_image_path,
        result_url=job.result_image_path,
        drive_link=job.drive_link,
        download_link=job.download_link,
        qr_url=job.qr_url,
        error_message=job.error_message,
        log_text=job.log_text,
    )
