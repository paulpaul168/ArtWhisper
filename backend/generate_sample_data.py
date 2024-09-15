import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Image, Audio
from app.auth import get_password_hash
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database connection
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/museum_db"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_or_create_user(
    db: SessionLocal, username: str, password: str, is_admin: bool = False
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(
            username=username,
            hashed_password=get_password_hash(password),
            is_admin=is_admin,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created new user: {username}")
    else:
        print(f"User already exists: {username}")
    return user


def add_example_data():
    db = SessionLocal()
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Add users
        admin_user = get_or_create_user(db, "admin", "adminpassword", is_admin=True)
        regular_user = get_or_create_user(db, "user", "userpassword")

        # Add images
        images = [
            Image(
                url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/1200px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg",
                title="Mona Lisa",
                description="The Mona Lisa is an oil painting by Italian artist, inventor, and writer Leonardo da Vinci. Likely completed in 1506, the piece features a portrait of a seated woman set against an imaginary landscape.",
                description_page="https://en.wikipedia.org/wiki/Mona_Lisa",
                artist="Leonardo da Vinci",
            ),
            Image(
                url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1200px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
                title="The Starry Night",
                description="The Starry Night is an oil-on-canvas painting by the Dutch Post-Impressionist painter Vincent van Gogh. Painted in June 1889, it depicts the view from the east-facing window of his asylum room at Saint-Rémy-de-Provence, just before sunrise, with the addition of an imaginary village.",
                description_page="https://en.wikipedia.org/wiki/The_Starry_Night",
                artist="Vincent van Gogh",
            ),
            Image(
                url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/The_Scream.jpg/1200px-The_Scream.jpg",
                title="The Scream",
                description="The Scream is the popular name given to a composition created by Norwegian Expressionist artist Edvard Munch in 1893. The agonized face in the painting has become one of the most iconic images of art, seen as symbolizing the anxiety of the human condition.",
                description_page="https://en.wikipedia.org/wiki/The_Scream",
                artist="Edvard Munch",
            ),
        ]

        # Check if images already exist
        existing_images = db.query(Image).all()
        existing_urls = [img.url for img in existing_images]

        for image in images:
            if image.url not in existing_urls:
                db.add(image)
                print(f"Added new image: {image.title}")
            else:
                print(f"Image already exists: {image.title}")

        db.commit()

        # Refresh images to get their IDs
        images = db.query(Image).all()

        # Add audio entries
        for image in images:
            existing_audio = (
                db.query(Audio)
                .filter(Audio.image_id == image.id, Audio.user_id == regular_user.id)
                .first()
            )
            if not existing_audio:
                audio = Audio(
                    filename=f"{image.title.lower().replace(' ', '_')}_audio.mp3",
                    user_id=regular_user.id,
                    image_id=image.id,
                    created_at=datetime.utcnow(),
                )
                db.add(audio)
                print(f"Added new audio for: {image.title}")
            else:
                print(f"Audio already exists for: {image.title}")

        db.commit()

        print("Example data added successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_example_data()
