from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional # Dict removed as mock_db_plays is gone
from datetime import datetime
import uuid

from echoread.api_server import models # SQLAlchemy models and Pydantic schemas
from echoread.api_server.database import get_db
from echoread.api_server.routers.users import get_current_user_mock
# _get_book_or_404 and _get_audio_or_404 are now used for validation
from echoread.api_server.routers.books import _get_book_or_404, _get_audio_or_404


# --- Router Definition ---
router = APIRouter(
    # prefix="/plays", # Prefix removed
    tags=["Playback"],
    dependencies=[Depends(get_current_user_mock)],
    responses={404: {"description": "Not found"}},
)

# Request model is models.PlayCreate, Response is models.PlayResponse

# --- Endpoints ---
@router.post("/plays", response_model=models.PlayResponse) # Path changed
async def save_play_position(
    request: models.PlayCreate, # Use Pydantic schema for request body
    current_user: models.User = Depends(get_current_user_mock), # SQLAlchemy User model
    db: Session = Depends(get_db)
):
    """
    Save or update the last playback position for a book's audio.
    """
    # Validate that the book and audio exist and belong to the user
    book = _get_book_or_404(db, request.book_id, current_user.id)
    audio = _get_audio_or_404(db, request.book_id, request.audio_id, current_user.id)

    # Check if a play record already exists for this user, book, and audio
    db_play = db.query(models.Play).filter(
        models.Play.user_id == current_user.id,
        models.Play.book_id == book.id, # Use validated book.id
        models.Play.audio_id == audio.id  # Use validated audio.id
    ).first()

    if db_play:
        # Update existing record
        db_play.last_timestamp = request.last_timestamp
        db_play.updated_at = datetime.utcnow() # Manually update timestamp
    else:
        # Create new record
        play_id = str(uuid.uuid4())
        db_play = models.Play(
            id=play_id,
            user_id=current_user.id,
            book_id=book.id,
            audio_id=audio.id,
            last_timestamp=request.last_timestamp,
            # created_at and updated_at have defaults / onupdate
        )
        db.add(db_play)

    db.commit()
    db.refresh(db_play)
    return db_play # Pydantic will convert using PlayResponse's from_attributes

@router.get("/play/{book_id}", response_model=List[models.PlayResponse]) # Path and response_model changed
async def get_last_play_position(
    book_id: str,
    current_user: models.User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Retrieve the most recently updated playback position for a specific book for the current user.
    Returns null if no position is saved for this book by this user.
    """
    # Validate that the book exists and belongs to the user
    _get_book_or_404(db, book_id, current_user.id)

    # Query for the most recently updated play record for this user and book
    # This assumes 'updated_at' correctly reflects the latest interaction.
    db_play = db.query(models.Play).filter(
        models.Play.user_id == current_user.id,
        models.Play.book_id == book_id
    ).order_by(models.Play.updated_at.desc()).first()

    if not db_play:
        return [] # Return empty list if not found

    return [db_play] # Return list with the found object
