from fastapi import APIRouter
from typing import List

from app.modules.themes.schema import ThemePublicOut, ThemeInternalOut
from app.modules.themes.service import list_themes_public, list_themes_internal

router = APIRouter(prefix="/themes", tags=["themes"])

@router.get("", response_model=List[ThemePublicOut])
def get_themes():
    return list_themes_public()

@router.get("/internal", response_model=List[ThemeInternalOut])
def get_themes_internal():
    return list_themes_internal()
