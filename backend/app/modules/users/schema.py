# Pydantic: UserCreate, UserOut
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    phone: str

class UserOut(UserCreate):
    id: int

    class Config:
        from_attributes = True
