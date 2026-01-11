from fastapi import APIRouter
from typing import List

from app.modules.themes.schema import ThemePublicOut
from app.modules.themes.service import list_themes_public

router = APIRouter(prefix="/themes", tags=["themes"])

@router.get("", response_model=List[ThemePublicOut])
def get_themes():
    return list_themes_public()
