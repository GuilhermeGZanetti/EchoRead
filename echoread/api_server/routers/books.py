from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from pydantic import BaseModel # Added for TTSStatusResponse
from typing import List, Dict, Optional
import uuid # For generating unique IDs for books
import time # For simulating processing time

# Import models from the main models.py
from .. import models
# Import mock authentication
from .users import get_current_user_mock # Assuming users.py is in the same directory

# --- Mock Database for Books & Audios ---
# In a real application, this would be a proper database.
mock_db_books: Dict[str, models.Book] = {}
# mock_db_audios stores a list of Audio models for each book_id
mock_db_audios: Dict[str, List[models.Audio]] = {}
# mock_db_tts_progress stores conceptual progress
mock_db_tts_progress: Dict[str, Dict] = {}


# --- Router Definition ---
router = APIRouter(
    prefix="/books",
    tags=["Books"],
    dependencies=[Depends(get_current_user_mock)], # Apply mock auth to all book routes
    responses={404: {"description": "Not found"}},
)

# --- Helper Functions ---
def _get_book_or_404(book_id: str, user_id: str) -> models.Book:
    book = mock_db_books.get(book_id)
    if not book or book.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book

def _get_audio_or_404(book_id: str, audio_id: str, user_id: str) -> models.Audio:
    _get_book_or_404(book_id, user_id) # Ensures book exists and belongs to user

    book_audios = mock_db_audios.get(book_id, [])
    audio = next((a for a in book_audios if a.id == audio_id), None)
    if not audio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio chapter not found")
    return audio

def _generate_mock_audio_for_book(book: models.Book, chapter_count: int = 5):
    """Generates mock audio entries for a book and updates its status."""
    audios = []

    mock_db_tts_progress[book.id] = {"processed_chapters": 0, "total_chapters": chapter_count, "status": "processing"}

    for i in range(1, chapter_count + 1):
        audio_id = f"audio_{book.id}_{i}" # More unique audio ID
        audio = models.Audio(
            id=audio_id,
            book_id=book.id,
            chapter_index=i,
            audio_path=f"/mock_audio_files/{book.id}/chapter_{i}.mp3", # Conceptual path
            url=f"/books/{book.id}/audios/{audio_id}", # Correct API path
            duration=180.0 + (i * 10), # Mock duration
            created_at=book.created_at # Align creation time for simplicity
        )
        audios.append(audio)
        mock_db_tts_progress[book.id]["processed_chapters"] = i

    mock_db_audios[book.id] = audios
    book.status = "complete"
    book.chapter_count = chapter_count
    mock_db_tts_progress[book.id]["status"] = "complete"


# --- Endpoints (Part 1 - Upload & Listing - From previous step) ---
@router.post("/upload", response_model=models.BookMetadata, status_code=status.HTTP_202_ACCEPTED)
async def upload_book(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user_mock)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    book_id = str(uuid.uuid4())
    book_title = file.filename.replace(".epub", "") if file.filename.endswith(".epub") else "Uploaded Book"

    new_book = models.Book(
        id=book_id,
        user_id=current_user.id,
        title=book_title,
        epub_path=f"/user_uploads/{current_user.id}/{file.filename}",
        status="processing",
        chapter_count=0
    )
    mock_db_books[book_id] = new_book

    _generate_mock_audio_for_book(new_book, chapter_count=5)

    return models.BookMetadata(
        id=new_book.id,
        title=new_book.title,
        created_at=new_book.created_at,
        status=new_book.status
    )

@router.get("", response_model=List[models.BookMetadata])
async def list_user_books(current_user: models.User = Depends(get_current_user_mock)):
    user_books = [
        models.BookMetadata(
            id=book.id,
            title=book.title,
            created_at=book.created_at,
            status=book.status
        )
        for book in mock_db_books.values() if book.user_id == current_user.id
    ]
    return user_books

@router.get("/{book_id}", response_model=models.BookDetail)
async def get_book_details(book_id: str, current_user: models.User = Depends(get_current_user_mock)):
    book = _get_book_or_404(book_id, current_user.id)
    return models.BookDetail(
        id=book.id,
        title=book.title,
        created_at=book.created_at,
        status=book.status,
        author="Mock Author",
        chapter_count=book.chapter_count
    )

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: str, current_user: models.User = Depends(get_current_user_mock)):
    _get_book_or_404(book_id, current_user.id)

    del mock_db_books[book_id]
    if book_id in mock_db_audios:
        del mock_db_audios[book_id]
    if book_id in mock_db_tts_progress:
        del mock_db_tts_progress[book_id]

    return None

# --- Endpoints (Part 2 - Audio & Status - Current step) ---

class TTSStatusResponse(BaseModel):
    book_id: str
    status: str
    processed_chapters: int
    total_chapters: int

@router.get("/{book_id}/status", response_model=TTSStatusResponse)
async def get_book_tts_status(book_id: str, current_user: models.User = Depends(get_current_user_mock)):
    """
    Get TTS generation progress for a book.
    """
    book = _get_book_or_404(book_id, current_user.id)
    progress = mock_db_tts_progress.get(book_id)

    if not progress:
        return TTSStatusResponse(
            book_id=book_id,
            status=book.status,
            processed_chapters=0,
            total_chapters=book.chapter_count or 0
        )

    return TTSStatusResponse(
        book_id=book_id,
        status=progress["status"],
        processed_chapters=progress["processed_chapters"],
        total_chapters=progress["total_chapters"]
    )

@router.get("/{book_id}/audios", response_model=List[models.AudioChapterInfo])
async def list_book_audios(book_id: str, current_user: models.User = Depends(get_current_user_mock)):
    """
    List all chapter audios for a specific book.
    """
    _get_book_or_404(book_id, current_user.id)

    book_audios_full = mock_db_audios.get(book_id, [])

    chapter_infos = [
        models.AudioChapterInfo(
            audio_id=audio.id,
            chapter_index=audio.chapter_index,
            url=audio.url,
            duration=audio.duration
        ) for audio in book_audios_full
    ]
    return chapter_infos

@router.get("/{book_id}/audios/{audio_id}")
async def get_book_chapter_audio(
    book_id: str,
    audio_id: str,
    current_user: models.User = Depends(get_current_user_mock)
):
    """
    Provide the mock audio data for a specific chapter.
    Returns MP3 data directly.
    """
    audio_obj = _get_audio_or_404(book_id, audio_id, current_user.id)

    mock_mp3_data = b"mock_mp3_data_for_" + audio_obj.id.encode('utf-8') + b"_chapter_" + str(audio_obj.chapter_index).encode('utf-8')

    return Response(content=mock_mp3_data, media_type="audio/mpeg")
