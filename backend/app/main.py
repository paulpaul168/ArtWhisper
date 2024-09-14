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
import cv2
import numpy as np
from pathlib import Path
import random
import pickle

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def test_find_similar_artwork():
    # Path to the test images folder
    test_images_folder = Path("test_images")
    
    # Get a list of all image files in the test folder
    test_images = list(test_images_folder.glob("*.jpg"))
    
    if not test_images:
        raise HTTPException(status_code=404, detail="No test images found")
    
    # Randomly select a test image
    test_image_path = random.choice(test_images)
    
    # Create a temporary UploadFile object
    with open(test_image_path, "rb") as image_file:
        temp_upload_file = UploadFile(filename=test_image_path.name, file=image_file)
        
        # Call the find_similar_artwork_endpoint function
        result = await find_similar_artwork_endpoint(temp_upload_file)
    
    return result

# Global variable to store the cached keypoints and descriptors
cached_paintings = {}

CACHE_FILE = 'paintings_cache.pkl'
PAINTINGS_FOLDER = Path("../crawler/belvedere_images")

def keypoints_to_list(keypoints):
    return [(kp.pt, kp.size, kp.angle, kp.response, kp.octave, kp.class_id) for kp in keypoints]

def list_to_keypoints(keypoints_list):
    return [cv2.KeyPoint(x=kp[0][0], y=kp[0][1], size=kp[1], angle=kp[2], response=kp[3], octave=kp[4], class_id=kp[5]) for kp in keypoints_list]

def load_or_compute_features():
    global cached_paintings
    
    if os.path.exists(CACHE_FILE):
        print("Loading cached features")
        try:
            with open(CACHE_FILE, 'rb') as f:
                cached_data = pickle.load(f)
            for painting_file, data in cached_data.items():
                cached_paintings[painting_file] = (list_to_keypoints(data['keypoints']), data['descriptors'])
            return
        except (EOFError, pickle.UnpicklingError, KeyError):
            print("Cache file is corrupted. Recomputing features.")
            os.remove(CACHE_FILE)
    
    print("Computing features for all paintings")
    sift = cv2.SIFT_create()
    
    for painting_file in PAINTINGS_FOLDER.glob("*.jpeg"):
        print(f"Processing {painting_file.name}")
        painting_image = cv2.imread(str(painting_file), cv2.IMREAD_GRAYSCALE)
        if painting_image is None:
            print(f"Failed to load image: {painting_file.name}")
            continue
        
        kp, des = sift.detectAndCompute(painting_image, None)
        cached_paintings[painting_file] = (kp, des)
    
    # Cache all computed features
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle_data = {k: {'keypoints': keypoints_to_list(v[0]), 'descriptors': v[1]} for k, v in cached_paintings.items()}
            pickle.dump(pickle_data, f)
        print("Features cached successfully")
    except Exception as e:
        print(f"Failed to cache features: {str(e)}")

@app.on_event("startup")
async def startup_event():
    load_or_compute_features()
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
async def find_similar_artwork_endpoint(image: UploadFile = File(...)):
    print(f"Received image: {image.filename}")
    
    # Save the uploaded image temporarily
    temp_image_path = "temp_uploaded_image.jpg"
    with open(temp_image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Load and preprocess the uploaded image
    query_image = cv2.imread(temp_image_path, cv2.IMREAD_GRAYSCALE)
    if query_image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Initialize SIFT detector
    sift = cv2.SIFT_create()
    
    # Detect keypoints and compute descriptors for the query image
    query_kp, query_des = sift.detectAndCompute(query_image, None)
    print(f"Query image keypoints: {len(query_kp)}")
    
    best_match = None
    best_score = 0
    
    # Match against all cached paintings
    for painting_file, (painting_kp, painting_des) in cached_paintings.items():
        # Match descriptors
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(query_des, painting_des, k=2)
        
        # Apply ratio test
        good_matches = [m for m, n in matches if m.distance < 0.4 * n.distance]
        
        # Calculate similarity score
        similarity_score = len(good_matches) / max(len(query_kp), len(painting_kp))
        
        if similarity_score > best_score:
            best_score = similarity_score
            best_match = painting_file.stem
            print(f"New best match: {best_match} with score: {best_score}")
    
    # Clean up temporary file
    os.remove(temp_image_path)
    
    if best_match:
        print(f"Final result: Best match {best_match} with similarity {best_score}")
        return {"similar_artwork_id": best_match, "similarity": best_score}
    else:
        print("No match found")
        return {"similar_artwork_id": None, "similarity": 0.0}

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
    return audio

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