from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

# === yang dipakai FE ===
class ThemePublicOut(BaseModel):
    id: str
    title: str
    thumbnail_url: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)

class ThemeInternalOut(BaseModel):
    id: str
    title: str
    thumbnail_url: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)

class ThemeInternal(BaseModel):
    id: str
    title: str
    thumbnail: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)

    def to_public(self) -> ThemePublicOut:
        return ThemePublicOut(
            id=self.id,
            title=self.title,
            thumbnail_url=self.thumbnail,
            params=self.params or {},
        )

    def to_internal(self) -> ThemeInternalOut:
        return ThemeInternalOut(
            id=self.id,
            title=self.title,
            thumbnail_url=self.thumbnail,
            prompt=self.prompt,
            negative_prompt=self.negative_prompt,
            params=self.params or {},
        )
