# app/modules/themes/service.py
import json
from pathlib import Path
import re
import unicodedata
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import THEMES_JSON, THUMBS_DIR
from app.modules.themes.model import Theme
from app.modules.themes.schema import ThemeInternal, ThemeInternalOut, ThemePublicOut
from app.utils.files import save_upload_file


def _theme_to_internal_out(theme: Theme) -> ThemeInternalOut:
    return ThemeInternalOut(
        id=theme.id,
        title=theme.title,
        thumbnail_url=theme.thumbnail_url,
        prompt=theme.prompt,
        negative_prompt=theme.negative_prompt,
        params=theme.params or {},
    )


def _theme_to_public_out(theme: Theme) -> ThemePublicOut:
    return ThemePublicOut(
        id=theme.id,
        title=theme.title,
        thumbnail_url=theme.thumbnail_url,
        params=theme.params or {},
    )


def _slugify_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "theme"


def _next_theme_id(db: Session, title: str) -> str:
    base = _slugify_title(title)
    if len(base) > 64:
        base = base[:64].rstrip("-")
    if not base:
        base = "theme"

    candidate = base
    counter = 2
    while db.get(Theme, candidate) is not None:
        suffix = f"-{counter}"
        max_base_len = 64 - len(suffix)
        prefix = base[:max_base_len].rstrip("-")
        candidate = f"{prefix}{suffix}" if prefix else f"theme{suffix}"
        counter += 1
    return candidate


def _next_theme_serial_id(db: Session) -> int:
    max_serial = db.query(func.max(Theme.serial_id)).scalar()
    return int(max_serial or 0) + 1


def _thumbnail_file_path_from_url(thumbnail_url: str | None) -> Path | None:
    if not thumbnail_url:
        return None

    prefix = "/static/thumbs/"
    if not thumbnail_url.startswith(prefix):
        return None

    filename = thumbnail_url[len(prefix) :].strip()
    if not filename:
        return None

    # keep deletion scoped strictly to THUMBS_DIR
    safe_name = Path(filename).name
    if not safe_name:
        return None

    return THUMBS_DIR / safe_name


def _load_seed_themes() -> List[ThemeInternal]:
    data = json.loads(THEMES_JSON.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("themes.json must contain a JSON array (list)")
    return [ThemeInternal(**item) for item in data]


def seed_themes_if_empty(db: Session) -> int:
    if db.query(Theme).first():
        return 0

    seeded = 0
    serial_counter = 0
    for item in _load_seed_themes():
        serial_counter += 1
        db.add(
            Theme(
                id=item.id,
                serial_id=serial_counter,
                title=item.title,
                thumbnail_url=item.thumbnail or "",
                prompt=item.prompt,
                negative_prompt=item.negative_prompt,
                params=item.params or {},
            )
        )
        seeded += 1

    db.commit()
    return seeded


def list_themes_public(db: Session) -> List[ThemePublicOut]:
    rows = (
        db.query(Theme)
        .order_by(Theme.serial_id.is_(None).asc(), Theme.serial_id.asc(), Theme.id.asc())
        .all()
    )
    return [_theme_to_public_out(t) for t in rows]


def list_themes_internal(db: Session) -> List[ThemeInternalOut]:
    rows = (
        db.query(Theme)
        .order_by(Theme.serial_id.is_(None).asc(), Theme.serial_id.asc(), Theme.id.asc())
        .all()
    )
    return [_theme_to_internal_out(t) for t in rows]


def get_theme_by_id(db: Session, theme_id: str) -> Optional[ThemeInternalOut]:
    row = db.get(Theme, theme_id)
    if row is None:
        return None
    return _theme_to_internal_out(row)


def create_theme(
    db: Session,
    *,
    title: str,
    prompt: str,
    negative_prompt: Optional[str],
    aspect_ratio: Optional[str],
    thumbnail_url: str,
) -> ThemeInternalOut:
    title_value = (title or "").strip()
    prompt_value = (prompt or "").strip()
    negative_prompt_value = (negative_prompt or "").strip() or None
    aspect_ratio_value = (aspect_ratio or "").strip() or "2:3"

    if not title_value:
        raise ValueError("THEME_TITLE_REQUIRED")
    if not prompt_value:
        raise ValueError("THEME_PROMPT_REQUIRED")
    if not thumbnail_url:
        raise ValueError("THEME_THUMBNAIL_REQUIRED")

    theme_id = _next_theme_id(db, title_value)

    created = Theme(
        id=theme_id,
        serial_id=_next_theme_serial_id(db),
        title=title_value,
        thumbnail_url=thumbnail_url,
        prompt=prompt_value,
        negative_prompt=negative_prompt_value,
        params={"aspect_ratio": aspect_ratio_value},
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return _theme_to_internal_out(created)


def create_theme_from_upload(
    db: Session,
    *,
    title: str,
    prompt: str,
    negative_prompt: Optional[str],
    aspect_ratio: Optional[str],
    thumbnail: UploadFile,
) -> ThemeInternalOut:
    if thumbnail is None:
        raise ValueError("THEME_THUMBNAIL_REQUIRED")
    if not (title or "").strip():
        raise ValueError("THEME_TITLE_REQUIRED")
    if not (prompt or "").strip():
        raise ValueError("THEME_PROMPT_REQUIRED")

    try:
        filename = save_upload_file(thumbnail, THUMBS_DIR)
    except ValueError as e:
        raise ValueError(str(e)) from e

    thumbnail_url = f"/static/thumbs/{filename}"

    try:
        return create_theme(
            db,
            title=title,
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            thumbnail_url=thumbnail_url,
        )
    except Exception:
        try:
            (THUMBS_DIR / filename).unlink(missing_ok=True)
        except Exception:
            pass
        raise


def update_theme(
    db: Session,
    *,
    theme_id: str,
    title: str,
    prompt: str,
    negative_prompt: Optional[str],
    aspect_ratio: Optional[str],
    thumbnail_url: Optional[str] = None,
) -> ThemeInternalOut:
    row = db.get(Theme, theme_id)
    if row is None:
        raise ValueError("THEME_NOT_FOUND")

    title_value = (title or "").strip()
    prompt_value = (prompt or "").strip()
    negative_prompt_value = (negative_prompt or "").strip() or None
    aspect_ratio_value = (aspect_ratio or "").strip() or "2:3"

    if not title_value:
        raise ValueError("THEME_TITLE_REQUIRED")
    if not prompt_value:
        raise ValueError("THEME_PROMPT_REQUIRED")

    row.title = title_value
    row.prompt = prompt_value
    row.negative_prompt = negative_prompt_value
    if thumbnail_url:
        row.thumbnail_url = thumbnail_url

    params = dict(row.params or {})
    params["aspect_ratio"] = aspect_ratio_value
    row.params = params

    db.commit()
    db.refresh(row)
    return _theme_to_internal_out(row)


def update_theme_from_upload(
    db: Session,
    *,
    theme_id: str,
    title: str,
    prompt: str,
    negative_prompt: Optional[str],
    aspect_ratio: Optional[str],
    thumbnail: Optional[UploadFile],
) -> ThemeInternalOut:
    thumbnail_url: Optional[str] = None
    filename: Optional[str] = None

    if thumbnail is not None:
        try:
            filename = save_upload_file(thumbnail, THUMBS_DIR)
        except ValueError as e:
            raise ValueError(str(e)) from e
        thumbnail_url = f"/static/thumbs/{filename}"

    try:
        return update_theme(
            db,
            theme_id=theme_id,
            title=title,
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            thumbnail_url=thumbnail_url,
        )
    except Exception:
        if filename:
            try:
                (THUMBS_DIR / filename).unlink(missing_ok=True)
            except Exception:
                pass
        raise


def delete_theme_by_id(db: Session, theme_id: str) -> None:
    row = db.get(Theme, theme_id)
    if row is None:
        raise ValueError("THEME_NOT_FOUND")

    thumbnail_url = row.thumbnail_url
    thumbnail_file = _thumbnail_file_path_from_url(thumbnail_url)

    db.delete(row)
    db.commit()

    if thumbnail_file:
        still_used = (
            db.query(Theme)
            .filter(Theme.thumbnail_url == thumbnail_url)
            .first()
            is not None
        )
        if still_used:
            return

        try:
            thumbnail_file.unlink(missing_ok=True)
        except Exception:
            pass
