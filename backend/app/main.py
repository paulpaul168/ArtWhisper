from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
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
from .image_detection import (
    load_or_compute_features,
    find_similar_artwork_endpoint,
)


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    load_or_compute_features()
    db = next(get_db())
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "secret!password")
    existing_admin = crud.get_user_by_username(db, admin_username)
    if not existing_admin:
        crud.create_admin_user(db, admin_username, admin_password)

    reload_audio_database(db)
    # Run the test function
    # print("Running test function...")
    # test_result = await test_find_similar_artwork()
    # print(f"Test result: {test_result}")


def reload_audio_database(db: Session):
    # Delete all existing audio entries
    db.query(models.Audio).delete()
    db.commit()

    # Get all audio files from the uploads folder
    uploads_folder = "uploads"
    audio_files = [f for f in os.listdir(uploads_folder) if f.startswith("audio_")]

    # Reload audio files into the database
    for audio_file in audio_files:
        # Extract information from the filename
        parts = audio_file.split("_")
        if len(parts) >= 4:
            image_id = int(parts[1])
            user_id = int(parts[2])

            # Create new audio entry
            audio_create = schemas.AudioCreate(filename=audio_file, image_id=image_id)
            crud.create_audio(db=db, audio=audio_create, user_id=user_id)

    print(f"Reloaded {len(audio_files)} audio files into the database.")


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
