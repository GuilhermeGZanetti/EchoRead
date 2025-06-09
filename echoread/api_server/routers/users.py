from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel # Ensure BaseModel is imported if needed for response_model or request body
from typing import Optional

# Import the User model from the main models file
# Assuming models.py is in the parent directory relative to routers/
# Adjust the import path if your structure is different or use absolute imports
from .. import models # Relative import for models.py

# --- Mock Authentication Dependency ---
# This is a placeholder for actual token validation.
# In a real app, this would involve decoding and verifying a JWT.
async def get_current_user_mock(token: Optional[str] = Depends(lambda x: x.headers.get("Authorization"))):
    if not token or not token.startswith("Bearer mock_jwt_token"): # Check for our mock token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Extract mock user identifier from the token (e.g., the email used as 'sub')
    try:
        # Example: "Bearer mock_jwt_token.timestamp.user@example.com"
        user_identifier = token.split(".")[-1]
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In a real app, you'd fetch user details from the database based on user_identifier
    # For this mock, we'll create a dummy User object
    mock_user = models.User(
        id=f"user_{hash(user_identifier)}", # Generate a mock ID
        email=user_identifier,
        name=user_identifier.split('@')[0].capitalize() # Generate a mock name
    )
    return mock_user

# --- Router Definition ---
router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

# --- Endpoint ---
@router.get("/me", response_model=models.User)
async def read_users_me(current_user: models.User = Depends(get_current_user_mock)):
    """
    Retrieve the profile of the currently authenticated user.
    """
    # The current_user is already a models.User instance from get_current_user_mock
    return current_user
