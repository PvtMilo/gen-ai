from pydantic import BaseModel
from typing import Any, Dict, Optional

class ThemeOut(BaseModel):
    id: str
    title: str
    thumbnail: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = None
    params: Dict[str, Any] = {}
