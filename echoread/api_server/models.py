from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    id: str = Field(default_factory=lambda: "user_" + str(hash(datetime.now()))[:6]) # Mock ID
    email: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Book(BaseModel):
    id: str = Field(default_factory=lambda: "book_" + str(hash(datetime.now()))[:6]) # Mock ID
    user_id: str
    title: str
    epub_path: Optional[str] = None # Conceptual path
    status: str = "pending" # e.g., pending, processing, complete, error
    chapter_count: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Audio(BaseModel):
    id: str = Field(default_factory=lambda: "audio_" + str(hash(datetime.now()))[:6]) # Mock ID
    book_id: str
    chapter_index: int
    audio_path: Optional[str] = None # Conceptual path to mock audio
    url: Optional[str] = None # URL to access this audio, e.g., /books/{book_id}/audios/{audio_id}
    duration: Optional[float] = None # Duration in seconds
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Play(BaseModel):
    id: str = Field(default_factory=lambda: "play_" + str(hash(datetime.now()))[:6]) # Mock ID
    user_id: str
    book_id: str
    audio_id: str
    last_timestamp: float # Playback position in seconds
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# For API responses (examples)
class BookMetadata(BaseModel):
    id: str
    title: str
    created_at: datetime
    status: str

class BookDetail(BookMetadata):
    author: Optional[str] = "Unknown Author" # Mocked for now
    chapter_count: Optional[int] = None

class AudioChapterInfo(BaseModel):
    audio_id: str
    chapter_index: int
    url: str
    duration: Optional[float] = None

class PlayPosition(BaseModel):
    book_id: str
    audio_id: str
    last_timestamp: float
    updated_at: datetime
