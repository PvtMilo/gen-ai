from sqlalchemy.orm import Session

from app.modules.users.model import User
from app.modules.sessions.model import PhotoSession
from app.modules.sessions.schema import SessionStartIn
from app.modules.themes.service import get_theme_by_id

def start_session(db: Session, payload: SessionStartIn) -> PhotoSession:
    # find-or-create user by email
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        user = User(name=payload.name, email=payload.email, phone=payload.phone)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # optional: sync latest input
        user.name = payload.name
        user.phone = payload.phone
        db.commit()

    s = PhotoSession(user_id=user.id, status="draft")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def set_session_theme(db: Session, session_id: int, theme_id: str) -> PhotoSession:
    s = db.query(PhotoSession).filter(PhotoSession.id == session_id).first()
    if s is None:
        raise ValueError("SESSION_NOT_FOUND")

    theme = get_theme_by_id(theme_id)
    if theme is None:
        raise ValueError("THEME_NOT_FOUND")

    s.theme_id = theme_id
    db.commit()
    db.refresh(s)
    return s