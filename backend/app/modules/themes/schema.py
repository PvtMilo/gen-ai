from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

# === yang dipakai FE ===
class ThemePublicOut(BaseModel):
    id: str
    title: str
    thumbnail_url: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)

# === yang dipakai backend (internal) ===
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
