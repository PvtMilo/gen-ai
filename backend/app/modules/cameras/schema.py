from pydantic import BaseModel


class CaptureResponse(BaseModel):
    photo_url: str
