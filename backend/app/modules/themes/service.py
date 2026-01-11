# app/modules/themes/service.py
import json
from typing import List, Optional

from app.core.config import THEMES_JSON
from app.modules.themes.schema import ThemeInternal, ThemePublicOut


def _load_themes_internal() -> List[ThemeInternal]:
    data = json.loads(THEMES_JSON.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("themes.json must contain a JSON array (list)")

    # ✅ convert dict -> ThemeInternal (punya method to_public)
    return [ThemeInternal(**item) for item in data]


def list_themes_public() -> List[ThemePublicOut]:
    return [t.to_public() for t in _load_themes_internal()]


def get_theme_by_id(theme_id: str) -> Optional[ThemeInternal]:
    for t in _load_themes_internal():
        if t.id == theme_id:
            return t
    return None
