from pydantic import BaseModel, EmailStr

class SessionStartIn(BaseModel):
    name: str
    email: EmailStr
    phone: str

class SessionStartOut(BaseModel):
    session_id: int
    user_id: int
    status: str

class SessionSetThemeIn(BaseModel):
    theme_id: str