import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool # For in-memory SQLite

from echoread.api_server.main import app # Main FastAPI app
from echoread.api_server.database import Base, get_db
from echoread.api_server import models # Import your SQLAlchemy models
import uuid
from datetime import datetime

# Setup for an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Mock user for dependency
MOCK_USER_ID = str(uuid.uuid4())
MOCK_USER_EMAIL = "test@example.com"
# This token format is based on the get_current_user_mock in echoread/api_server/routers/users.py
# It expects "Bearer mock_jwt_token.<email>"
MOCK_AUTH_TOKEN = f"Bearer mock_jwt_token.{MOCK_USER_EMAIL}"

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine) # Create tables
    # Pre-populate with a mock user, as get_current_user_mock might try to fetch/create one
    db = TestingSessionLocal()
    user = db.query(models.User).filter(models.User.email == MOCK_USER_EMAIL).first()
    if not user:
        user = models.User(id=MOCK_USER_ID, email=MOCK_USER_EMAIL, name="Test User")
        db.add(user)
        db.commit()
    # else: # If user exists, ensure MOCK_USER_ID matches what's in DB for consistency if needed
    #    global MOCK_USER_ID # Not ideal, but for fixture simplicity if ID must match pre-existing
    #    MOCK_USER_ID = user.id
    db.close()
    yield
    Base.metadata.drop_all(bind=engine) # Drop tables after test


# --- Test for GET /books/{book_id} ---
def test_get_book_details_includes_author():
    db = TestingSessionLocal()
    book_id = str(uuid.uuid4())
    test_book = models.Book(
        id=book_id,
        user_id=MOCK_USER_ID,
        title="Test Book with Author",
        author="Test Author"
    )
    db.add(test_book)
    db.commit()
    db.close()

    response = client.get(f"/books/{book_id}", headers={"Authorization": MOCK_AUTH_TOKEN})
    if response.status_code != 200:
        print("Response JSON for unexpected status code:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["author"] == "Test Author"
    assert data["title"] == "Test Book with Author"

def test_get_book_details_defaults_author():
    db = TestingSessionLocal()
    book_id = str(uuid.uuid4())
    # Author field is omitted, should default
    test_book = models.Book(id=book_id, user_id=MOCK_USER_ID, title="Test Book No Author")
    db.add(test_book)
    db.commit()
    db.close()

    response = client.get(f"/books/{book_id}", headers={"Authorization": MOCK_AUTH_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert data["author"] == "Unknown Author" # Default value from Pydantic model

# --- Test for GET /books/{book_id}/audios/{audio_id} ---
def test_get_book_chapter_audio_url():
    db = TestingSessionLocal()
    book_id = str(uuid.uuid4())
    audio_id = "audio_" + str(uuid.uuid4()) # Match Audio model default id prefix if any

    test_book = models.Book(id=book_id, user_id=MOCK_USER_ID, title="Audio Test Book")
    db.add(test_book)
    db.commit()

    test_audio = models.Audio(
        id=audio_id,
        book_id=book_id,
        chapter_index=1,
        audio_path="/test/path.mp3", # Example path
        url=f"/books/{book_id}/audios/{audio_id}", # Example URL, though API generates its own
        duration=180.0
    )
    db.add(test_audio)
    db.commit()
    db.close()

    response = client.get(f"/books/{book_id}/audios/{audio_id}", headers={"Authorization": MOCK_AUTH_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert f"https://api.echoread.com/media/books/{book_id}/chapters/{audio_id}.mp3?token=mock_presigned_token" == data["url"]
    assert data["expires_in"] == 3600

# --- Test for GET /play/{book_id} ---
def test_get_last_play_position_found():
    db = TestingSessionLocal()
    book_id = str(uuid.uuid4())
    # Need a valid audio_id for the Play record, create a dummy audio too
    audio_id = "audio_" + str(uuid.uuid4())

    test_book = models.Book(id=book_id, user_id=MOCK_USER_ID, title="Play Test Book")
    db.add(test_book)
    # Create a dummy audio record for FK integrity if Play.audio_id has a constraint
    # that is checked when creating Play record.
    # (Assuming Audio model's id is generated like "audio_uuid_string")
    dummy_audio = models.Audio(id=audio_id, book_id=book_id, chapter_index=0)
    db.add(dummy_audio)
    db.commit()

    play_id = "play_" + str(uuid.uuid4()) # Match Play model default id prefix
    test_play = models.Play(
        id=play_id,
        user_id=MOCK_USER_ID,
        book_id=book_id,
        audio_id=audio_id,
        last_timestamp=123.45,
        updated_at=datetime.utcnow() # Ensure it's the latest
    )
    db.add(test_play)
    db.commit()
    db.close()

    response = client.get(f"/play/{book_id}", headers={"Authorization": MOCK_AUTH_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    play_record = data[0]
    assert play_record["book_id"] == book_id
    assert play_record["audio_id"] == audio_id
    assert play_record["last_timestamp"] == 123.45

def test_get_last_play_position_not_found():
    db = TestingSessionLocal()
    book_id = str(uuid.uuid4())
    # Ensure book exists for the _get_book_or_404 check in the endpoint
    test_book = models.Book(id=book_id, user_id=MOCK_USER_ID, title="Play Test Book No Play")
    db.add(test_book)
    db.commit()
    db.close()

    response = client.get(f"/play/{book_id}", headers={"Authorization": MOCK_AUTH_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_last_play_position_book_not_found():
    non_existent_book_id = str(uuid.uuid4())
    response = client.get(f"/play/{non_existent_book_id}", headers={"Authorization": MOCK_AUTH_TOKEN})
    # This endpoint calls _get_book_or_404 first.
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Book not found" # Or whatever your 404 detail is
