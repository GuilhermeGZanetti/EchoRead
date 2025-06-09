from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import time

from echoread.api_server import models
from echoread.api_server.models import AudioURLResponse # Import the new model
from echoread.api_server.database import get_db
from echoread.api_server.routers.users import get_current_user_mock

# --- Router Definition ---
router = APIRouter(
    prefix="/books",
    tags=["Books"],
    dependencies=[Depends(get_current_user_mock)],
    responses={404: {"description": "Not found"}},
)

# --- Helper Functions ---
def _get_book_or_404(db: Session, book_id: str, user_id: str) -> models.Book:
    book = db.query(models.Book).filter(models.Book.id == book_id, models.Book.user_id == user_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book

def _get_audio_or_404(db: Session, book_id: str, audio_id: str, user_id: str) -> models.Audio:
    # First, ensure the book itself exists and belongs to the user
    book = _get_book_or_404(db, book_id, user_id)
    # Now, query for the audio related to this book
    audio = db.query(models.Audio).filter(models.Audio.id == audio_id, models.Audio.book_id == book.id).first()
    if not audio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio chapter not found")
    return audio

def _generate_and_save_audios_for_book(db: Session, book: models.Book, chapter_count: int = 5):
    """Generates SQLAlchemy Audio objects for a book and adds them to the session."""
    # This function now creates SQLAlchemy Audio objects.
    # The actual audio file generation/TTS is still conceptual.

    # book.audios will be an empty list initially as per relationship setup

    for i in range(1, chapter_count + 1):
        audio_id = str(uuid.uuid4()) # Generate unique ID for each audio
        new_audio = models.Audio(
            id=audio_id,
            book_id=book.id,
            chapter_index=i,
            audio_path=f"/user_uploads/{book.user_id}/{book.id}/chapter_{i}.mp3", # Conceptual path
            url=f"/books/{book.id}/audios/{audio_id}", # API path to access this audio
            duration=180.0 + (i * 10), # Mock duration
            # created_at is default in model
        )
        db.add(new_audio) # Add to session; book.audios will be populated by SQLAlchemy
        # No need to append to book.audios manually if back_populates is correct

    book.status = "complete" # Update book status
    book.chapter_count = chapter_count # Update chapter count
    db.add(book) # Mark book as dirty to save status/chapter_count updates


# --- Endpoints ---
@router.post("/upload", response_model=models.BookResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_book(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    book_id = str(uuid.uuid4())
    book_title = file.filename.replace(".epub", "") if file.filename.endswith(".epub") else "Uploaded Book"

    db_book = models.Book(
        id=book_id,
        user_id=current_user.id,
        title=book_title,
        epub_path=f"/user_uploads/{current_user.id}/{file.filename}",
        status="processing",
    )
    db.add(db_book)

    # Generate and associate audio entries
    _generate_and_save_audios_for_book(db, db_book, chapter_count=5) # Example: 5 chapters

    db.commit()
    db.refresh(db_book)
    # To ensure audios are loaded for the response if BookResponse includes them (it doesn't currently)
    # If BookResponse were to include audios, you might need db.refresh(db_book.audios) or similar
    # or ensure the session is configured to load them. For now, BookResponse is simple.

    return db_book

@router.get("", response_model=List[models.BookResponse])
async def list_user_books(
    current_user: models.User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    user_books = db.query(models.Book).filter(models.Book.user_id == current_user.id).all()
    return user_books

@router.get("/{book_id}", response_model=models.BookDetail) # Using BookDetail for richer info
async def get_book_details(
    book_id: str,
    current_user: models.User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    book = _get_book_or_404(db, book_id, current_user.id)
    # book.audios relationship will be loaded by SQLAlchemy (lazy load by default)
    # Pydantic's BookDetail (with from_attributes=True) will handle serialization
    return book # book object now includes its audios through relationship

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: str,
    current_user: models.User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    book = _get_book_or_404(db, book_id, current_user.id)
    # Cascade delete should handle associated audios and plays (if Play has FK to Book and cascade)
    db.delete(book)
    db.commit()
    return None

# --- Endpoints (Part 2 - Audio & Status) ---

class TTSStatusResponse(PydanticBaseModel):
    book_id: str
    status: str # e.g., "pending", "processing", "complete", "error"
    processed_chapters: int # Number of audio chapters generated
    total_chapters: int # Expected total chapters (can be from book.chapter_count)

@router.get("/{book_id}/status", response_model=TTSStatusResponse)
async def get_book_tts_status(
    book_id: str,
    current_user: models.User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    book = _get_book_or_404(db, book_id, current_user.id)

    # `processed_chapters` can be the count of audio objects associated with the book.
    # `total_chapters` can be what's stored in `book.chapter_count`.
    # This provides a more realistic status based on DB data.
    processed_chapters_count = len(book.audios) # Relies on relationship loading

    return TTSStatusResponse(
        book_id=book.id,
        status=book.status,
        processed_chapters=processed_chapters_count,
        total_chapters=book.chapter_count or 0
    )

@router.get("/{book_id}/audios", response_model=List[models.AudioChapterInfo])
async def list_book_audios(
    book_id: str,
    current_user: models.User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    book = _get_book_or_404(db, book_id, current_user.id)
    # book.audios is a list of SQLAlchemy Audio objects.
    # These will be converted to AudioChapterInfo by Pydantic.
    return book.audios

@router.get("/{book_id}/audios/{audio_id}", response_model=AudioURLResponse)
async def get_book_chapter_audio(
    book_id: str,
    audio_id: str,
    current_user: models.User = Depends(get_current_user_mock), # current_user is available if needed for logic
    db: Session = Depends(get_db) # db session is available if needed
):
    # Ensure the audio chapter exists and belongs to the user's book (indirectly via book_id and user_id)
    _ = _get_audio_or_404(db, book_id, audio_id, current_user.id) # We don't need audio_obj here

    # Construct the URL as specified
    url = f"https://api.echoread.com/media/books/{book_id}/chapters/{audio_id}.mp3?token=mock_presigned_token"
    expires_in = 3600 # As specified

    return AudioURLResponse(url=url, expires_in=expires_in)
