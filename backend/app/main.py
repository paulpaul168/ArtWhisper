from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from . import crud, models, schemas, auth
from .database import engine, get_db
import shutil
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "secret!password")
    existing_admin = crud.get_user_by_username(db, admin_username)
    if not existing_admin:
        crud.create_admin_user(db, admin_username, admin_password)

@app.post("/images", response_model=schemas.Image)
async def create_image(
    file: UploadFile = File(...),
    description: str = Form(...),
    author: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Save the uploaded file
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Create image in database
    image_data = schemas.ImageCreate(
        filename=file.filename,
        description=description,
        author=author
    )
    return crud.create_image(db, image_data)

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
def change_password(new_password: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    current_user.hashed_password = auth.get_password_hash(new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@app.get("/audio/{image_id}")
def get_audio(image_id: int, db: Session = Depends(get_db)):
    image = crud.get_image(db, image_id=image_id)
    if not image or not image.audio_filename:
        raise HTTPException(status_code=404, detail="Audio not found")
    return {"audio_filename": image.audio_filename}

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
    current_user: models.User = Depends(auth.get_current_user)
):
    image = crud.get_image(db, image_id=image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    audio_filename = f"audio_{image_id}_{current_user.id}_{audio.filename}"
    with open(f"uploads/{audio_filename}", "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
    
    audio_create = schemas.AudioCreate(filename=audio_filename, image_id=image_id)
    return crud.create_audio(db=db, audio=audio_create, user_id=current_user.id)

@app.get("/audio/{audio_id}", response_model=schemas.Audio)
def get_audio(audio_id: int, db: Session = Depends(get_db)):
    audio = crud.get_audio(db, audio_id=audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    return audio

@app.get("/image/{image_id}/audios", response_model=list[schemas.Audio])
def get_audios_for_image(image_id: int, db: Session = Depends(get_db)):
    return crud.get_audios_for_image(db, image_id=image_id)

@app.get("/user/audios", response_model=list[schemas.Audio])
def get_user_audios(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_audios_for_user(db, user_id=current_user.id)