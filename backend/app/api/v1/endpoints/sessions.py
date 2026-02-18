from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import UPLOADS_DIR

from app.modules.sessions.schema import (
    SessionStartIn,
    SessionSetThemeIn,
    SessionOut,
    UserOut,
)
from app.modules.sessions.service import start_session, set_session_theme
from app.modules.sessions.model import PhotoSession

from app.modules.users.model import User
from app.modules.jobs.model import Job
from app.modules.jobs.schema import JobOut

from app.utils.files import save_upload_file

router = APIRouter(prefix="/sessions", tags=["sessions"])


def build_session_out(db: Session, s: PhotoSession) -> SessionOut:
    user = db.query(User).filter(User.id == s.user_id).first()
    if not user:
        raise HTTPException(status_code=500, detail="User missing for this session")

    latest = (
        db.query(Job)
        .filter(Job.session_id == s.id)
        .order_by(Job.id.desc())
        .first()
    )

    latest_job = None
    if latest:
        latest_job = JobOut(
            job_id=latest.id,
            session_id=latest.session_id,
            status=latest.status,
            mode=latest.mode or "event",
            overlay_url=latest.overlay_image_path,
            result_url=latest.result_image_path,
            error_message=latest.error_message,
        )

    return SessionOut(
        session_id=s.id,
        status=s.status,
        user=UserOut(id=user.id, name=user.name, email=user.email, phone=user.phone),
        theme_id=s.theme_id,
        input_image_url=s.input_image_path,
        latest_job=latest_job,
    )


@router.post("/start", response_model=SessionOut)
def start(payload: SessionStartIn, db: Session = Depends(get_db)):
    s = start_session(db, payload)
    db.refresh(s)
    return build_session_out(db, s)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    s = db.query(PhotoSession).filter(PhotoSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_session_out(db, s)


@router.patch("/{session_id}/theme", response_model=SessionOut)
def patch_theme(session_id: int, payload: SessionSetThemeIn, db: Session = Depends(get_db)):
    try:
        s = set_session_theme(db, session_id=session_id, theme_id=payload.theme_id)

        # OPTIONAL: update status biar jelas untuk FE
        if s.status == "draft":
            s.status = "theme_selected"
            db.commit()
            db.refresh(s)

        return build_session_out(db, s)

    except ValueError as e:
        if str(e) == "SESSION_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Session not found")
        if str(e) == "THEME_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Theme not found")
        raise


@router.post("/{session_id}/upload", response_model=SessionOut)
def upload_photo(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    s = db.query(PhotoSession).filter(PhotoSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    filename = save_upload_file(file, UPLOADS_DIR)

    s.input_image_path = f"/static/uploads/{filename}"

    # OPTIONAL: update status biar jelas untuk FE
    if s.status in ("draft", "theme_selected"):
        s.status = "photo_uploaded"

    db.commit()
    db.refresh(s)

    return build_session_out(db, s)
