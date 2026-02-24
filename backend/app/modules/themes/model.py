from sqlalchemy import Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    serial_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(120))
    thumbnail_url: Mapped[str] = mapped_column(String(255))
    prompt: Mapped[str] = mapped_column(Text)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
