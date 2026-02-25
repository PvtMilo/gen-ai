import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from PIL import Image, ImageOps

from app.db.session import SessionLocal
from app.modules.jobs.model import Job
from app.modules.sessions.model import PhotoSession
from app.modules.themes.service import get_theme_by_id

from app.core.config import (
    APP_DIR,
    RESULTS_DIR,
    OVERLAYS_DIR,
    COMPRESSED_DIR,
    COMPRESSED_TARGET_SIZE,
    COMPRESSED_FORMAT,
    COMPRESSED_EXTENSION,
    COMPRESSED_QUALITY,
    COMPRESSED_DPI,
    DRIVE_UPLOAD_SOURCE,
    SEEDDREAM_SIZE,
    SEEDDREAM_WATERMARK,
)
from app.utils.encode import file_to_data_url
from app.utils.files import save_image_from_url

RESAMPLE_LANCZOS = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS


def _normalize_mode(mode: str | None) -> str:
    return "debugging" if mode == "debugging" else "event"


def _resolve_overlay_abs(overlay_url: str | None) -> Path | None:
    if not overlay_url:
        return None
    if not overlay_url.startswith("/static/overlays/"):
        raise ValueError("OVERLAY_INVALID")
    rel = overlay_url.lstrip("/")
    abs_path = (APP_DIR / rel).resolve()
    overlays_root = OVERLAYS_DIR.resolve()
    if overlays_root not in abs_path.parents:
        raise ValueError("OVERLAY_INVALID")
    if abs_path.suffix.lower() != ".png":
        raise ValueError("OVERLAY_INVALID")
    if not abs_path.exists() or not abs_path.is_file():
        raise ValueError("OVERLAY_NOT_FOUND")
    return abs_path


def create_job(
    db: Session,
    session_id: int,
    mode: str = "event",
    overlay_url: str | None = None,
) -> Job:
    s = db.query(PhotoSession).filter(PhotoSession.id == session_id).first()
    if not s:
        raise ValueError("SESSION_NOT_FOUND")
    if not s.theme_id:
        raise ValueError("THEME_NOT_SET")
    if not s.input_image_path:
        raise ValueError("PHOTO_NOT_UPLOADED")

    _resolve_overlay_abs(overlay_url)

    job = Job(
        session_id=session_id,
        mode=_normalize_mode(mode),
        overlay_image_path=overlay_url,
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _resolve_job_static_path(static_path: str | None) -> Path | None:
    if not static_path:
        return None

    rel = static_path.lstrip("/")
    abs_path = (APP_DIR / rel).resolve()
    app_root = APP_DIR.resolve()
    if app_root not in abs_path.parents:
        return None
    return abs_path


def _resolve_drive_upload_path(job: Job) -> tuple[Path, str]:
    raw_path = _resolve_job_static_path(job.result_image_path)
    compressed_path = _resolve_job_static_path(job.compressed_image_path)

    if DRIVE_UPLOAD_SOURCE == "compressed":
        if compressed_path and compressed_path.exists():
            return compressed_path, "compressed"
        if raw_path and raw_path.exists():
            return raw_path, "results"
        raise ValueError("RESULT_FILE_NOT_FOUND")

    if raw_path and raw_path.exists():
        return raw_path, "results"
    raise ValueError("RESULT_FILE_NOT_FOUND")


def _attach_drive_info(db: Session, job: Job) -> None:
    try:
        from app.integrations.gdrive.service import upload_file_to_drive
    except Exception as e:
        print(f"[JOB {job.id}] GDRIVE IMPORT FAILED: {e}")
        return

    try:
        file_path, source = _resolve_drive_upload_path(job)
        print(f"[JOB {job.id}] GDRIVE SOURCE: {source} path={file_path}")
        uploaded = upload_file_to_drive(file_path)
        job.drive_file_id = uploaded.get("file_id")
        job.drive_link = uploaded.get("drive_link")
        job.download_link = uploaded.get("download_link")
        job.qr_url = uploaded.get("qr_url")
        job.drive_uploaded_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        print(f"[JOB {job.id}] GDRIVE OK ({source}): {job.drive_link}")
    except ValueError as e:
        print(f"[JOB {job.id}] GDRIVE SKIPPED: {e}")
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
        try:
            file_path, source = _resolve_drive_upload_path(job)
        except ValueError:
            continue

        print(f"[JOB {job.id}] DRIVE SYNC SOURCE: {source} path={file_path}")
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


def upload_drive_link_for_job(
    db: Session,
    *,
    job_id: int,
    force: bool = False,
) -> dict:
    try:
        from app.integrations.gdrive.client import get_drive_service
        from app.integrations.gdrive.service import upload_file_to_drive
    except Exception as e:
        raise RuntimeError(f"GDRIVE_IMPORT_FAILED: {e}") from e

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError("JOB_NOT_FOUND")

    if not job.result_image_path:
        raise ValueError("RESULT_NOT_FOUND")

    if (
        not force
        and job.drive_file_id
        and job.drive_link
        and job.qr_url
    ):
        return {
            "job_id": job.id,
            "result_url": job.result_image_path,
            "drive_link": job.drive_link,
            "download_link": job.download_link,
            "qr_url": job.qr_url,
            "uploaded": False,
            "message": "already_uploaded",
        }

    try:
        file_path, source = _resolve_drive_upload_path(job)
    except ValueError:
        raise ValueError("RESULT_FILE_NOT_FOUND")

    print(f"[JOB {job.id}] DRIVE UPLOAD SOURCE: {source} path={file_path}")
    service = get_drive_service()
    uploaded = upload_file_to_drive(file_path, service=service)

    job.drive_file_id = uploaded.get("file_id")
    job.drive_link = uploaded.get("drive_link")
    job.download_link = uploaded.get("download_link")
    job.qr_url = uploaded.get("qr_url")
    job.drive_uploaded_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "result_url": job.result_image_path,
        "drive_link": job.drive_link,
        "download_link": job.download_link,
        "qr_url": job.qr_url,
        "uploaded": True,
        "message": "uploaded",
    }

def _generate_event_result(input_abs: Path, prompt: str, *, logger, started_at: float) -> Path:
    # Keep these steps isolated so overlay can be inserted later after this stage.
    logger("encoding image")
    image_data_url = file_to_data_url(input_abs)

    logger("calling api")
    from app.integrations.seeddream_client import generate_i2i_url

    result_url = generate_i2i_url(
        prompt=prompt,
        image_data_url=image_data_url,
        size=SEEDDREAM_SIZE,
        watermark=SEEDDREAM_WATERMARK,
    )

    logger("api done")

    if time.time() - started_at > 180:
        raise RuntimeError("Job timeout >180s (processing took too long)")

    return save_image_from_url(
        result_url,
        RESULTS_DIR,
        ext=".jpg",
        attempts=5,
        connect_timeout=10,
        read_timeout=180,
        logger=logger,
        label="downloading",
        progress_step=10,
    )


def _generate_debug_result(input_abs: Path, *, logger) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ext = input_abs.suffix.lower() if input_abs.suffix else ".jpg"
    saved = RESULTS_DIR / f"{uuid.uuid4().hex}{ext}"
    shutil.copy2(input_abs, saved)
    logger("debug mode: copied captured image")
    return saved


def _bake_overlay(result_abs: Path, overlay_abs: Path, *, logger) -> Path:
    logger("overlay: loading files")
    with Image.open(result_abs) as result_img:
        result_img.load()
        result_w, result_h = result_img.size
        result_rgba = result_img.convert("RGBA")

    with Image.open(overlay_abs) as overlay_img:
        overlay_img.load()
        overlay_w, overlay_h = overlay_img.size
        overlay_rgba = overlay_img.convert("RGBA")

    logger(f"overlay: result={result_w}x{result_h}, overlay={overlay_w}x{overlay_h}")

    if (overlay_w, overlay_h) == (result_w, result_h):
        fitted_overlay = overlay_rgba
        logger("overlay: size matched")
    else:
        src_ratio = overlay_w / overlay_h
        dst_ratio = result_w / result_h
        if abs(src_ratio - dst_ratio) < 1e-6:
            fitted_overlay = overlay_rgba.resize((result_w, result_h), RESAMPLE_LANCZOS)
            logger(f"overlay: resized to {result_w}x{result_h}")
        else:
            # Fallback for unexpected ratio mismatch while avoiding stretch.
            contained = ImageOps.contain(
                overlay_rgba,
                (result_w, result_h),
                method=RESAMPLE_LANCZOS,
            )
            fitted_overlay = Image.new("RGBA", (result_w, result_h), (0, 0, 0, 0))
            offset_x = (result_w - contained.width) // 2
            offset_y = (result_h - contained.height) // 2
            fitted_overlay.paste(contained, (offset_x, offset_y), contained)
            logger("overlay: ratio mismatch, fitted without stretch")

    logger("overlay: baking")
    composed = Image.alpha_composite(result_rgba, fitted_overlay)

    out_path = RESULTS_DIR / f"{uuid.uuid4().hex}.png"
    # Save final composite as PNG so we do not add extra lossy JPEG compression.
    composed.save(out_path, format="PNG", optimize=False, compress_level=3)
    logger("overlay: done")
    return out_path


def _save_compressed_copy(final_result_abs: Path, *, logger) -> Path:
    COMPRESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = COMPRESSED_DIR / f"{final_result_abs.stem}{COMPRESSED_EXTENSION}"

    logger(
        f"compression: target={COMPRESSED_TARGET_SIZE[0]}x{COMPRESSED_TARGET_SIZE[1]} "
        f"format={COMPRESSED_FORMAT} quality={COMPRESSED_QUALITY}"
    )
    with Image.open(final_result_abs) as src:
        src.load()
        rgb = src.convert("RGB")
        resized = rgb.resize(COMPRESSED_TARGET_SIZE, RESAMPLE_LANCZOS)
        resized.save(
            output,
            format=COMPRESSED_FORMAT,
            quality=COMPRESSED_QUALITY,
            optimize=True,
            dpi=COMPRESSED_DPI,
        )

    logger(f"compression: saved {output.name}")
    return output


def process_job_seeddream_safe(job_id: int, requested_mode: str | None = None) -> None:
    db: Session = SessionLocal()
    started_at = time.time()
    job: Job | None = None

    def mark_failed(msg: str):
        job2 = db.query(Job).filter(Job.id == job_id).first()
        if job2:
            job2.status = "failed"
            job2.error_message = msg
            db.commit()

    def log_line(message: str) -> None:
        nonlocal job
        print(message)
        try:
            job2 = job or db.query(Job).filter(Job.id == job_id).first()
            if not job2:
                return
            job = job2
            if job2.log_text:
                job2.log_text = f"{job2.log_text}\n{message}"
            else:
                job2.log_text = message
            db.commit()
        except Exception:
            pass

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            log_line("job not found")
            return

        mode = _normalize_mode(requested_mode or job.mode)
        job.status = "processing"
        job.mode = mode
        job.log_text = None
        db.commit()
        db.refresh(job)

        log_line(f"processing mode={mode}")


        session = db.query(PhotoSession).filter(PhotoSession.id == job.session_id).first()
        if not session or not session.theme_id or not session.input_image_path:
            mark_failed("Session not ready (theme/photo missing)")
            log_line("failed: session not ready")
            return

        theme = get_theme_by_id(db, session.theme_id)
        if not theme:
            mark_failed("Theme not found")
            log_line("failed: theme not found")
            return

        rel = session.input_image_path.lstrip("/")          # static/uploads/xxx.jpeg
        input_abs = APP_DIR / rel                           # backend/app/static/uploads/xxx.jpeg

        if not input_abs.exists():
            mark_failed(f"Input file not found: {input_abs}")
            log_line("failed: input file missing")
            return

        try:
            if mode == "debugging":
                saved = _generate_debug_result(input_abs, logger=log_line)
            else:
                saved = _generate_event_result(
                    input_abs,
                    theme.prompt,
                    logger=log_line,
                    started_at=started_at,
                )
        except Exception as e:
            mark_failed(str(e))
            log_line("failed: generate")
            return

        overlay_abs = _resolve_overlay_abs(job.overlay_image_path)
        if overlay_abs:
            try:
                baked = _bake_overlay(saved, overlay_abs, logger=log_line)
                if baked != saved and saved.exists():
                    try:
                        saved.unlink()
                    except Exception:
                        pass
                saved = baked
            except Exception as e:
                mark_failed(str(e))
                log_line("failed: overlay")
                return
        else:
            log_line("overlay: skipped")

        compressed_rel_path = None
        try:
            compressed_saved = _save_compressed_copy(saved, logger=log_line)
            compressed_rel_path = f"/static/compressed/{compressed_saved.name}"
        except Exception as e:
            log_line(f"compression: failed ({e})")

        job2 = db.query(Job).filter(Job.id == job_id).first()
        if not job2:
            log_line("job missing before final commit")
            return

        job2.status = "done"
        job2.mode = mode
        job2.result_image_path = f"/static/results/{saved.name}"
        job2.compressed_image_path = compressed_rel_path
        db.commit()
        db.refresh(job2)

        log_line("done")

        _attach_drive_info(db, job2)

    except Exception as e:
        log_line(f"failed: {e}")
        try:
            mark_failed(str(e))
        except Exception:
            pass
    finally:
        db.close()
