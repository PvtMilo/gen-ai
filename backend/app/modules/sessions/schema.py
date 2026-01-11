from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str

class JobOut(BaseModel):
    job_id: int
    session_id: int
    status: Literal["queued", "processing", "done", "failed"]
    result_url: Optional[str] = None
    error_message: Optional[str] = None

class SessionStartIn(BaseModel):
    name: str
    email: EmailStr
    phone: str

class SessionSetThemeIn(BaseModel):
    theme_id: str

class SessionOut(BaseModel):
    session_id: int
    status: str
    user: UserOut
    theme_id: Optional[str] = None
    input_image_url: Optional[str] = None
    latest_job: Optional[JobOut] = None
