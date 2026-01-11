from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.sessions.schema import SessionStartIn, SessionStartOut, SessionSetThemeIn
from app.modules.sessions.service import start_session, set_session_theme
from app.utils.files import save_image_from_url
from app.core.config import UPLOADS_DIR
from app.modules.sessions.model import PhotoSession
from app.utils.files import save_upload_file

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/start", response_model=SessionStartOut)
def start(payload: SessionStartIn, db: Session = Depends(get_db)):
    s = start_session(db, payload)
    return SessionStartOut(session_id=s.id, user_id=s.user_id, status=s.status)

@router.patch("/{session_id}/theme")
def patch_theme(session_id: int, payload: SessionSetThemeIn, db: Session = Depends(get_db)):
    try:
        s = set_session_theme(db, session_id=session_id, theme_id=payload.theme_id)
        return {"session_id": s.id, "theme_id": s.theme_id, "status": s.status}
    except ValueError as e:
        if str(e) == "SESSION_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Session not found")
        if str(e) == "THEME_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Theme not found")
        raise


@router.post("/{session_id}/upload")
def upload_photo(session_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    s = db.query(PhotoSession).filter(PhotoSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    filename = save_upload_file(file, UPLOADS_DIR)

    # Simpan path relatif yang nanti bisa dipakai FE
    s.input_image_path = f"/static/uploads/{filename}"
    db.commit()
    db.refresh(s)

    return {"session_id": s.id, "photo_url": s.input_image_path}