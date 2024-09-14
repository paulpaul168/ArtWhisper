from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
    Form,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sqlalchemy
from . import crud, models, schemas, auth
from datetime import datetime
from .database import engine, get_db
import shutil
import os

from typing import List
import tensorflow as tf
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


models.Base.metadata.create_all(bind=engine)

model = tf.keras.models.load_model('../embedding_generator/art_feature_extractor.h5')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/find-similar-artwork", response_model=schemas.SimilarArtworkResponse)
async def find_similar_artwork(image: UploadFile = File(...)):
    contents = await image.read()
    embedding = await calculate_embedding(contents)
    
    all_embeddings = crud.get_all_artwork_embeddings()
    similarities = cosine_similarity([embedding], [e['embedding'] for e in all_embeddings])[0]
    
    most_similar_idx = np.argmax(similarities)
    most_similar_id = all_embeddings[most_similar_idx]['id']
    highest_similarity = similarities[most_similar_idx]
    
    if highest_similarity >= 0.8:  # You can adjust this threshold
        return {"similar_artwork_id": most_similar_id, "similarity": float(highest_similarity)}
    else:
        return {"similar_artwork_id": None, "similarity": float(highest_similarity)}

async def calculate_embedding(image_contents: bytes) -> List[float]:
    image = tf.image.decode_image(image_contents, channels=3)
    image = tf.image.resize(image, (224, 224))
    image = tf.expand_dims(image, axis=0)
    image = tf.cast(image, tf.float32) / 255.0
    
    embedding = model.predict(image)
    return np.array(embedding[0]).tolist()

@app.post("/calculate-embedding", response_model=List[float])
async def calculate_embedding_endpoint(file: UploadFile = File(...)):
    contents = await file.read()
    return await calculate_embedding(contents)

@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "secret!password")
    existing_admin = crud.get_user_by_username(db, admin_username)
    if not existing_admin:
        crud.create_admin_user(db, admin_username, admin_password)


@app.post("/images/{image_id}", response_model=schemas.Image)
async def create_image(
    image_id: int,
    image: schemas.ImageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Internal: Create a new image entry with a specific ID.

    - **image_id**: The ID to use for the new image
    - **image**: Image data including URL, title, description, description page URL, and author
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        return crud.create_image(db, image, image_id)
    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(status_code=409, detail="Item already exists")


@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    - **user**: User information including username and password
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.post("/token")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Authenticate a user and return an access token.

    - **user**: User credentials including username and password
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/change-password")
def change_password(
    new_password: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change the password for the currently authenticated user.

    - **new_password**: The new password to set
    """
    current_user.hashed_password = auth.get_password_hash(new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@app.get("/images/{image_id}", response_model=schemas.Image)
def get_image(image_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific image by its ID.

    - **image_id**: The ID of the image to retrieve
    """
    db_image = crud.get_image(db, image_id=image_id)
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return db_image


@app.post("/upload-audio/{image_id}", response_model=schemas.Audio)
def upload_audio(
    image_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Upload an audio file for a specific image.

    - **image_id**: ID of the image to associate the audio with
    - **audio**: The audio file to upload
    """
    image = crud.get_image(db, image_id=image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    audio_filename = (
        f"audio_{image_id}_{current_user.id}_{current_time}_{audio.filename}"
    )

    with open(f"uploads/{audio_filename}", "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    audio_create = schemas.AudioCreate(filename=audio_filename, image_id=image_id)
    return crud.create_audio(db=db, audio=audio_create, user_id=current_user.id)


@app.get("/audio/{audio_id}", response_model=schemas.Audio)
def get_audio(audio_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific audio entry by its ID.

    - **audio_id**: The ID of the audio to retrieve
    """
    audio = crud.get_audio(db, audio_id=audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    return audio


@app.get("/image/{image_id}/audios", response_model=list[schemas.Audio])
def get_audios_for_image(
    image_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Retrieve audios for a specific image with pagination.

    - **image_id**: ID of the image to get audios for
    - **skip**: Number of audios to skip (for pagination)
    - **limit**: Maximum number of audios to return (for pagination)
    """
    return crud.get_audios_for_image(db, image_id=image_id, skip=skip, limit=limit)


@app.get("/user/audios", response_model=list[schemas.Audio])
def get_user_audios(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Retrieve all audios uploaded by the currently authenticated user.
    """
    return crud.get_audios_for_user(db, user_id=current_user.id)

@app.get("/artwork-embeddings", response_model=list[schemas.ArtworkEmbedding])
def get_artwork_embeddings():
    """
    Retrieve embeddings for all artworks.
    """
    return crud.get_all_artwork_embeddings()