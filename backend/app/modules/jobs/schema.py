from pydantic import BaseModel

class JobCreateIn(BaseModel):
    session_id: int

class JobOut(BaseModel):
    job_id: int
    session_id: int
    status: str
    result_url: str | None = None
    drive_link: str | None = None
    download_link: str | None = None
    qr_url: str | None = None
    error_message: str | None = None
