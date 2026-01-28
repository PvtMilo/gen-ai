import shutil
import time
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.modules.jobs.model import Job
from app.modules.sessions.model import PhotoSession
from app.modules.themes.service import get_theme_by_id

from app.core.config import APP_DIR, RESULTS_DIR, SEEDDREAM_SIZE, SEEDDREAM_WATERMARK
from app.utils.encode import file_to_data_url
from app.integrations.seeddream_client import generate_i2i_url
from app.utils.files import save_image_from_url


def create_job(db: Session, session_id: int) -> Job:
    s = db.query(PhotoSession).filter(PhotoSession.id == session_id).first()
    if not s:
        raise ValueError("SESSION_NOT_FOUND")
    if not s.theme_id:
        raise ValueError("THEME_NOT_SET")
    if not s.input_image_path:
        raise ValueError("PHOTO_NOT_UPLOADED")

    job = Job(session_id=session_id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _attach_drive_info(db: Session, job: Job, file_path: Path) -> None:
    try:
        from app.integrations.gdrive.service import upload_file_to_drive
    except Exception as e:
        print(f"[JOB {job.id}] GDRIVE IMPORT FAILED: {e}")
        return

    try:
        uploaded = upload_file_to_drive(file_path)
        job.drive_file_id = uploaded.get("file_id")
        job.drive_link = uploaded.get("drive_link")
        job.download_link = uploaded.get("download_link")
        job.qr_url = uploaded.get("qr_url")
        job.drive_uploaded_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        print(f"[JOB {job.id}] GDRIVE OK: {job.drive_link}")
    except Exception as e:
        print(f"[JOB {job.id}] GDRIVE FAILED: {e}")


def sync_drive_links(
    db: Session,
    *,
    limit: int | None = None,
    force: bool = False,
) -> list[dict]:
    try:
        from app.integrations.gdrive.client import get_drive_service
        from app.integrations.gdrive.service import upload_file_to_drive
    except Exception as e:
        raise RuntimeError(f"GDRIVE_IMPORT_FAILED: {e}") from e

    query = db.query(Job).filter(Job.result_image_path.isnot(None))
    if not force:
        query = query.filter(Job.drive_link.is_(None))
    query = query.order_by(Job.id.desc())
    if limit and limit > 0:
        query = query.limit(limit)

    service = get_drive_service()
    results: list[dict] = []

    for job in query.all():
        rel = job.result_image_path.lstrip("/")
        file_path = APP_DIR / rel
        if not file_path.exists():
            continue

        uploaded = upload_file_to_drive(file_path, service=service)
        job.drive_file_id = uploaded.get("file_id")
        job.drive_link = uploaded.get("drive_link")
        job.download_link = uploaded.get("download_link")
        job.qr_url = uploaded.get("qr_url")
        job.drive_uploaded_at = datetime.utcnow()
        db.commit()
        db.refresh(job)

        results.append(
            {
                "job_id": job.id,
                "result_url": job.result_image_path,
                "drive_link": job.drive_link,
                "download_link": job.download_link,
                "qr_url": job.qr_url,
            }
        )

    return results


def process_job_dummy_safe(job_id: int) -> None:
    """
    AMAN: bikin SessionLocal sendiri di background thread.
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        # simulasi loading 2 detik
        time.sleep(2)

        session = db.query(PhotoSession).filter(PhotoSession.id == job.session_id).first()
        if not session or not session.input_image_path:
            job.status = "failed"
            job.error_message = "Session photo missing"
            db.commit()
            return

        # input_image_path contoh: /static/uploads/xxx.jpeg
        input_rel = session.input_image_path.lstrip("/")  # static/uploads/xxx.jpeg
        input_abs = Path("app") / input_rel               # app/static/uploads/xxx.jpeg

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out_name = f"result_job_{job.id}.jpeg"
        out_abs = RESULTS_DIR / out_name

        shutil.copy2(input_abs, out_abs)

        job.status = "done"
        job.result_image_path = f"/static/results/{out_name}"
        db.commit()
        _attach_drive_info(db, job, out_abs)

    except Exception as e:
        # fallback: mark failed (kalau job record masih ada)
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def process_job_seeddream_safe(job_id: int) -> None:
    db: Session = SessionLocal()
    started_at = time.time()

    def mark_failed(msg: str):
        job2 = db.query(Job).filter(Job.id == job_id).first()
        if job2:
            job2.status = "failed"
            job2.error_message = msg
            db.commit()

    try:
        print(f"[JOB {job_id}] START")

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print(f"[JOB {job_id}] job not found")
            return

        job.status = "processing"
        db.commit()
        db.refresh(job)


        session = db.query(PhotoSession).filter(PhotoSession.id == job.session_id).first()
        if not session or not session.theme_id or not session.input_image_path:
            mark_failed("Session not ready (theme/photo missing)")
            print(f"[JOB {job_id}] FAILED: session not ready")
            return

        theme = get_theme_by_id(session.theme_id)
        if not theme:
            mark_failed("Theme not found")
            print(f"[JOB {job_id}] FAILED: theme not found")
            return

        rel = session.input_image_path.lstrip("/")          # static/uploads/xxx.jpeg
        input_abs = APP_DIR / rel                           # backend/app/static/uploads/xxx.jpeg
        print(f"[JOB {job_id}] input_abs={input_abs}")

        if not input_abs.exists():
            mark_failed(f"Input file not found: {input_abs}")
            print(f"[JOB {job_id}] FAILED: file not found")
            return

        # -------- checkpoint: encode base64
        print(f"[JOB {job_id}] ENCODING IMAGE...")
        image_data_url = file_to_data_url(input_abs)
        print(f"[JOB {job_id}] ENCODE OK, data_url_len={len(image_data_url)}")

        prompt = theme.prompt

        # -------- checkpoint: call seeddream
        print(f"[JOB {job_id}] CALLING SEEDDREAM...")
        t0 = time.time()

        result_url = generate_i2i_url(
            prompt=prompt,
            image_data_url=image_data_url,
            size=SEEDDREAM_SIZE,
            watermark=SEEDDREAM_WATERMARK,
        )

        dt = time.time() - t0
        print(f"[JOB {job_id}] SEEDDREAM RETURNED in {dt:.1f}s")
        print(f"[JOB {job_id}] result_url={result_url}")

        # hard timeout (opsional)
        if time.time() - started_at > 180:
            raise RuntimeError("Job timeout >180s (processing took too long)")

        print(f"[JOB {job_id}] DOWNLOADING RESULT...")
        try:
            saved = save_image_from_url(
                result_url,
                RESULTS_DIR,
                ext=".jpg",
                attempts=5,
                connect_timeout=10,
                read_timeout=180,
                log_prefix=f"[JOB {job_id}] DOWNLOAD",
                progress_step=10,
            )
        except Exception as e:
            mark_failed(str(e))
            print(f"[JOB {job_id}] DOWNLOAD FAILED: {e}")
            return

        print(f"[JOB {job_id}] SAVED RESULT: {saved.name}")

        job2 = db.query(Job).filter(Job.id == job_id).first()
        if not job2:
            print(f"[JOB {job_id}] job missing before final commit")
            return

        job2.status = "done"
        job2.result_image_path = f"/static/results/{saved.name}"
        db.commit()
        db.refresh(job2)

        print(f"[JOB {job_id}] DONE DB: status={job2.status}, result={job2.result_image_path}")

        _attach_drive_info(db, job2, RESULTS_DIR / saved.name)

    except Exception as e:
        print(f"[JOB {job_id}] ERROR: {e}")
        try:
            mark_failed(str(e))
        except Exception:
            pass
    finally:
        db.close()
