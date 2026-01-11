from fastapi import APIRouter
from typing import List

from app.modules.themes.schema import ThemeOut
from app.modules.themes.service import list_themes

router = APIRouter(prefix="/themes", tags=["themes"])

@router.get("", response_model=List[ThemeOut])
def get_themes():
    return list_themes()
