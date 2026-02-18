from pydantic import BaseModel
from typing import Literal

class JobCreateIn(BaseModel):
    session_id: int
    mode: Literal["event", "debugging"] = "event"
    overlay_url: str | None = None

class JobOut(BaseModel):
    job_id: int
    session_id: int
    status: str
    mode: Literal["event", "debugging"] = "event"
    overlay_url: str | None = None
    result_url: str | None = None
    drive_link: str | None = None
    download_link: str | None = None
    qr_url: str | None = None
    error_message: str | None = None
    log_text: str | None = None
