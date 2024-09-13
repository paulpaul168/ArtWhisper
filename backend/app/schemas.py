from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False

class User(BaseModel):
    id: int
    username: str
    is_admin: bool 

    class Config:
        from_attributes = True

class ImageCreate(BaseModel):
    url: str
    title: str  
    description: str
    description_page: str 
    author: str

class Image(ImageCreate):
    id: int

    class Config:
        from_attributes = True

class AudioCreate(BaseModel):
    filename: str
    image_id: int

class Audio(AudioCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str