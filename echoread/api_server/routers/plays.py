from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional
from datetime import datetime

# Import models from the main models.py
from .. import models
# Import mock authentication
from .users import get_current_user_mock
# Import book helpers to check if book exists (optional, but good practice)
# Ensure this relative import path is correct based on your file structure.
# If books.py is in the same directory as plays.py (both under 'routers'), this is fine.
from .books import _get_book_or_404

# --- Mock Database for Play Positions ---
# Key: user_id, Value: Dict[book_id, models.Play]
mock_db_plays: Dict[str, Dict[str, models.Play]] = {}

# --- Router Definition ---
router = APIRouter(
    prefix="/plays",
    tags=["Playback"],
    dependencies=[Depends(get_current_user_mock)],
    responses={404: {"description": "Not found"}},
)

# --- Request Models (if different from main models) ---
class SavePlayPositionRequest(models.BaseModel): # Use pydantic BaseModel
    book_id: str
    audio_id: str # The specific chapter/audio file being played
    last_timestamp: float # Playback position in seconds

# --- Endpoints ---
@router.post("", response_model=models.PlayPosition)
async def save_play_position(
    request: SavePlayPositionRequest,
    current_user: models.User = Depends(get_current_user_mock)
):
    """
    Save the last playback position for a book's audio.
    """
    # Validate that the book exists and belongs to the user
    _get_book_or_404(request.book_id, current_user.id)
    # In a real app, you might also validate audio_id against available audios for the book

    play_id = f"play_{current_user.id}_{request.book_id}" # Simple unique ID for this mock

    play_data = models.Play(
        id=play_id,
        user_id=current_user.id,
        book_id=request.book_id,
        audio_id=request.audio_id,
        last_timestamp=request.last_timestamp,
        updated_at=datetime.utcnow()
    )

    if current_user.id not in mock_db_plays:
        mock_db_plays[current_user.id] = {}
    mock_db_plays[current_user.id][request.book_id] = play_data

    return models.PlayPosition(
        book_id=play_data.book_id,
        audio_id=play_data.audio_id,
        last_timestamp=play_data.last_timestamp,
        updated_at=play_data.updated_at
    )

@router.get("/{book_id}", response_model=Optional[models.PlayPosition])
async def get_last_play_position(
    book_id: str,
    current_user: models.User = Depends(get_current_user_mock)
):
    """
    Retrieve the last saved playback position for a specific book for the current user.
    Returns null if no position is saved.
    """
    # Validate that the book exists and belongs to the user
    _get_book_or_404(book_id, current_user.id)

    user_plays = mock_db_plays.get(current_user.id)
    if not user_plays:
        return None

    play_data = user_plays.get(book_id)
    if not play_data:
        return None

    return models.PlayPosition(
        book_id=play_data.book_id,
        audio_id=play_data.audio_id,
        last_timestamp=play_data.last_timestamp,
        updated_at=play_data.updated_at
    )
