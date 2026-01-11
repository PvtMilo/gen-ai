import json
from pathlib import Path
from typing import List, Optional

from app.modules.themes.schema import ThemeOut

def _themes_file_path() -> Path:
    # .../backend/app/modules/themes/data/themes.json
    return Path(__file__).resolve().parent / "data" / "themes.json"

def list_themes() -> List[ThemeOut]:
    path = _themes_file_path()
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    return [ThemeOut(**item) for item in raw]

def get_theme_by_id(theme_id: str) -> Optional[ThemeOut]:
    for theme in list_themes():
        if theme.id == theme_id:
            return theme
    return None
