from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("photo_sessions.id"), index=True)

    mode: Mapped[str] = mapped_column(String(20), default="event")
    overlay_image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|processing|done|failed
    result_image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    compressed_image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    log_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    drive_file_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    drive_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    download_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    qr_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    drive_uploaded_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
