from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import time # For dummy JWT generation

# --- Pydantic Models for Auth ---
class GoogleTokenRequest(BaseModel):
    token: str # This would be the Google OAuth2 token

class JWTResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LogoutResponse(BaseModel):
    message: str = "Successfully logged out"

# --- Router Definition ---
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)

# --- Mock JWT Generation ---
# In a real app, use python-jose or similar libraries
def create_mock_jwt(data: dict) -> str:
    # This is a highly simplified mock. Real JWTs have a specific structure and signature.
    return f"mock_jwt_token.{{time.time()}}.{{data.get('sub', 'unknown_user')}}" # Escaped curly braces for f-string

# --- Endpoints ---
@router.post("/google", response_model=JWTResponse)
async def login_google(request: GoogleTokenRequest):
    '''
    Mock exchanging a Google OAuth2 token for our app's JWT.
    In a real scenario, you would validate the Google token here.
    '''
    if not request.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token cannot be empty",
        )

    # Mock user info extracted from a validated Google token
    mock_user_email = "user@example.com" # Simulate extracting email

    # Create a mock JWT for our application
    # The 'sub' (subject) claim typically holds the user identifier
    access_token = create_mock_jwt(data={"sub": mock_user_email})
    return JWTResponse(access_token=access_token)

@router.post("/logout", response_model=LogoutResponse)
async def logout():
    '''
    Mock invalidating the current JWT.
    In a stateless JWT setup, true server-side invalidation is complex.
    Often, this means client-side token deletion and possibly a short-lived token blacklist.
    For this mock, we just return a success message.
    '''
    # In a real app:
    # - Add token to a blacklist (e.g., in Redis) until it expires.
    # - Client should delete the token.
    return LogoutResponse(message="Successfully logged out (mocked)")
