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
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import sqlalchemy
from . import crud, models, schemas, auth
from datetime import datetime
from .database import engine, get_db
import shutil
import os

from typing import List
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np

from .image_processing import process_image, find_similar_artwork
from .image_module import load_images_from_folder, index_database


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load and index the database images (do this at app startup)
database_folder = '../crawler/belvedere_images'
database_images = load_images_from_folder(database_folder)
kmeans, index = index_database(database_images)

class ProgressMiniBatchKMeans(MiniBatchKMeans):
    def fit(self, X, y=None, sample_weight=None):
        self.n_iter = 100  # Adjust this based on your needs
        batch_size = min(1000, len(X) // 10)  # Adjust batch size as needed
        for i in tqdm(range(self.n_iter), desc="MiniBatchKMeans clustering"):
            if i == 0:
                super().partial_fit(X, y, sample_weight)
            else:
                super().partial_fit(X, y, sample_weight)
        return self

@app.post("/find-similar-artwork", response_model=schemas.SimilarArtworkResponse)
async def find_similar_artwork_endpoint(image: UploadFile = File(...)):
    contents = await image.read()
    processed_artworks, _ = process_image(contents)
    
    best_result = None
    highest_similarity = -1

    for artwork in processed_artworks:
        result = find_similar_artwork(artwork, database_images, kmeans, index)
        if result and result['similarity'] > highest_similarity:
            best_result = result
            highest_similarity = result['similarity']
    
    if best_result:
        return {"similar_artwork_id": best_result['similar_artwork_id'], "similarity": best_result['similarity']}
    else:
        return {"similar_artwork_id": None, "similarity": 0.0}

@app.post("/calculate-embeddings", response_model=List[List[float]])
async def calculate_embeddings_endpoint(file: UploadFile = File(...)):
    contents = await file.read()
    return calculate_embeddings(contents)

@app.on_event("startup")
async def startup_event():
    #test_image_processing()
    db = next(get_db())
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "secret!password")
    existing_admin = crud.get_user_by_username(db, admin_username)
    if not existing_admin:
        crud.create_admin_user(db, admin_username, admin_password)
     # Run the test function
    print("Running test function...")
    test_result = await test_find_similar_artwork()
    print(f"Test result: {test_result}")

@app.post("/find-similar-artwork", response_model=schemas.SimilarArtworkResponse)
async def find_similar_artwork(image: UploadFile = File(...)):
    return await find_similar_artwork_endpoint(image)


@app.post("/images/{image_id}", response_model=schemas.Image)
async def create_image(
    image_id: int,
    image: schemas.ImageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        return crud.create_image(db, image, image_id)
    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(status_code=409, detail="Item already exists")

@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
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
    current_user.hashed_password = auth.get_password_hash(new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@app.get("/images/{image_id}", response_model=schemas.Image)
def get_image(image_id: int, db: Session = Depends(get_db)):
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

@app.get("/audio/{audio_id}")
def get_audio_file(audio_id: int, db: Session = Depends(get_db)):
    audio = crud.get_audio(db, audio_id=audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    file_path = f"uploads/{audio.filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(file_path, media_type="audio/ogg", filename=audio.filename)

@app.get("/image/{image_id}/audios", response_model=list[schemas.Audio])
def get_audios_for_image(
    image_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return crud.get_audios_for_image(db, image_id=image_id, skip=skip, limit=limit)

@app.get("/user/audios", response_model=list[schemas.Audio])
def get_user_audios(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.get_audios_for_user(db, user_id=current_user.id)

@app.get("/artwork-embeddings", response_model=list[schemas.ArtworkEmbedding])
def get_artwork_embeddings():
    return crud.get_all_artwork_embeddings()
