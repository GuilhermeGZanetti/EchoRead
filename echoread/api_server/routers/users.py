from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid # For generating user IDs if needed

from echoread.api_server import models # SQLAlchemy models and Pydantic models/schemas
from echoread.api_server.database import get_db # Database session dependency

# --- Mock Authentication Dependency (Updated) ---
# This is a placeholder. In a real app, this would involve decoding and verifying a JWT,
# then fetching the user from the DB based on 'sub' or similar claim.
async def get_current_user_mock(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(lambda x: x.headers.get("Authorization"))
):
    if not token or not token.startswith("Bearer mock_jwt_token"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_email = token.split(".")[-1] # Mock: email is the last part of the token
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format for mock user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    if not db_user:
        # For this mock, if user doesn't exist, create them.
        # In a real scenario, you might only allow existing users.
        user_id = str(uuid.uuid4())
        db_user = models.User(
            id=user_id,
            email=user_email,
            name=user_email.split('@')[0].capitalize()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return db_user

# --- Router Definition ---
router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

# --- Endpoint ---
@router.get("/me", response_model=models.UserResponse) # Use Pydantic response model
async def read_users_me(current_user: models.User = Depends(get_current_user_mock)):
    """
    Retrieve the profile of the currently authenticated user.
    """
    # current_user is an SQLAlchemy User model instance.
    # Pydantic's UserResponse will convert it based on Config.from_attributes = True.
    return current_user
