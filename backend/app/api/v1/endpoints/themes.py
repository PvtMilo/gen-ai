from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from typing import List
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.themes.schema import ThemePublicOut, ThemeInternalOut
from app.modules.themes.service import (
    create_theme_from_upload,
    delete_theme_by_id,
    get_theme_by_id,
    list_themes_internal,
    list_themes_public,
    update_theme_from_upload,
)

router = APIRouter(prefix="/themes", tags=["themes"])

@router.get("", response_model=List[ThemePublicOut])
def get_themes(db: Session = Depends(get_db)):
    return list_themes_public(db)

@router.get("/internal", response_model=List[ThemeInternalOut])
def get_themes_internal(db: Session = Depends(get_db)):
    return list_themes_internal(db)


@router.get("/internal/{theme_id}", response_model=ThemeInternalOut)
def get_theme_internal_by_id(theme_id: str, db: Session = Depends(get_db)):
    theme = get_theme_by_id(db, theme_id)
    if theme is None:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@router.post("", response_model=ThemeInternalOut)
def post_theme(
    title: str = Form(...),
    prompt: str = Form(...),
    negative_prompt: str | None = Form(None),
    aspect_ratio: str | None = Form("2:3"),
    thumbnail: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        return create_theme_from_upload(
            db,
            title=title,
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            thumbnail=thumbnail,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "THEME_TITLE_REQUIRED":
            raise HTTPException(status_code=400, detail="Theme title is required")
        if msg == "THEME_PROMPT_REQUIRED":
            raise HTTPException(status_code=400, detail="Theme prompt is required")
        if msg == "THEME_THUMBNAIL_REQUIRED":
            raise HTTPException(status_code=400, detail="Theme thumbnail is required")
        if msg == "INVALID_FILE_TYPE":
            raise HTTPException(status_code=400, detail="Thumbnail must be .jpg/.jpeg/.png/.webp")
        raise


@router.patch("/{theme_id}", response_model=ThemeInternalOut)
def patch_theme(
    theme_id: str,
    title: str = Form(...),
    prompt: str = Form(...),
    negative_prompt: str | None = Form(None),
    aspect_ratio: str | None = Form("2:3"),
    thumbnail: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    try:
        return update_theme_from_upload(
            db,
            theme_id=theme_id,
            title=title,
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            thumbnail=thumbnail,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "THEME_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Theme not found")
        if msg == "THEME_TITLE_REQUIRED":
            raise HTTPException(status_code=400, detail="Theme title is required")
        if msg == "THEME_PROMPT_REQUIRED":
            raise HTTPException(status_code=400, detail="Theme prompt is required")
        if msg == "INVALID_FILE_TYPE":
            raise HTTPException(status_code=400, detail="Thumbnail must be .jpg/.jpeg/.png/.webp")
        raise


@router.delete("/{theme_id}", status_code=204)
def delete_theme(theme_id: str, db: Session = Depends(get_db)):
    try:
        delete_theme_by_id(db, theme_id)
    except ValueError as e:
        msg = str(e)
        if msg == "THEME_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Theme not found")
        raise

    return Response(status_code=204)
