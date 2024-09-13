from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)

    audios = relationship("Audio", back_populates="user")

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    description = Column(String)
    title = Column(String)
    description_page = Column(String)
    artist = Column(String)

    audios = relationship("Audio", back_populates="image")

class Audio(Base):
    __tablename__ = "audios"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_id = Column(Integer, ForeignKey("images.id"))
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="audios")
    image = relationship("Image", back_populates="audios")