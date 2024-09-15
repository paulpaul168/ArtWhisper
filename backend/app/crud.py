from sqlalchemy.orm import Session
from . import models, schemas, auth
from json import load


def get_all_artwork_embeddings():
    with open("../embedding_generator/art_embeddings.json", "r") as f:
        embeddings = load(f)

    return [
        {"id": image_name.split(".")[0], "embedding": embedding}
        for image_name, embedding in embeddings.items()
    ]


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username, hashed_password=hashed_password, is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_admin_user(db: Session, username: str, password: str):
    admin_user = schemas.UserCreate(username=username, password=password, is_admin=True)
    return create_user(db, admin_user)


def create_image(db: Session, image: schemas.ImageCreate, image_id: int):
    db_image = models.Image(id=image_id, **image.dict())
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def get_image(db: Session, image_id: int):
    return db.query(models.Image).filter(models.Image.id == image_id).first()


def create_audio(db: Session, audio: schemas.AudioCreate, user_id: int):
    db_audio = models.Audio(**audio.dict(), user_id=user_id)
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio


def get_audio(db: Session, audio_id: int):
    return db.query(models.Audio).filter(models.Audio.id == audio_id).first()


def get_audios_for_image(db: Session, image_id: int, skip: int = 0, limit: int = 10):
    return (
        db.query(models.Audio)
        .filter(models.Audio.image_id == image_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_audios_for_user(db: Session, user_id: int):
    return db.query(models.Audio).filter(models.Audio.user_id == user_id).all()
