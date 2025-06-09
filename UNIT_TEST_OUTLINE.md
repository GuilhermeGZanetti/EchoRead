# Unit Test Outline for EchoRead API Server Database Interactions

## Testing Strategy:
*   **Scope:** Focus on testing the service/router layer logic.
*   **Database:** Utilize a mock database session or an in-memory SQLite database for fast, isolated tests.
    *   For SQLite, ensure compatibility with any PostgreSQL-specific features if used (though current models are fairly generic).
*   **Operations:** Test CRUD (Create, Read, Update, Delete) operations for each SQLAlchemy model.
*   **Business Logic:** Verify specific logic within router functions, such as conditional creation/updates, handling of non-existent entities, and user-specific data access.
*   **Relationships & Cascades:** Test how model relationships are handled (e.g., loading related objects, cascade deletions).
*   **Authentication & Authorization:** While full auth tests might be separate, unit tests for routers should mock authentication (like `get_current_user_mock`) to provide a `current_user` context. Test that data access is correctly scoped to this user.

## Key Areas for Unit Tests:

### 1. `echoread/api_server/database.py`
*   **`get_db` function:**
    *   Verify it yields a SQLAlchemy `Session`.
    *   Verify the session is closed after the context (more of an integration concern, but can be mocked).
    *   (Primary testing of `get_db` is through its usage in endpoint tests with dependency overrides).

### 2. `echoread/api_server/models.py` (Model-specific Logic)
*   **Default Value Generation:**
    *   Test `id` default factories (e.g., `Audio.id`, `Play.id`) ensure unique string IDs are generated.
    *   Test `created_at` and `updated_at` default/onupdate timestamps.
*   **Relationships (Primarily tested via router logic):**
    *   Verify `back_populates` are correctly configured (indirectly tested via CRUD that involves relationships).
    *   Verify `cascade="all, delete-orphan"` behavior (e.g., deleting a `User` also deletes their `Book`s and `Play`s; deleting a `Book` also deletes its `Audio`s).

### 3. `echoread/api_server/routers/users.py`
*   **`get_current_user_mock` (with DB interaction):**
    *   **New User:** When token's user email is not in DB:
        *   A new `User` record is created in the database.
        *   The new `User` object is returned.
    *   **Existing User:** When token's user email exists in DB:
        *   The existing `User` record is fetched from the database.
        *   No new user is created.
        *   The existing `User` object is returned.
*   **`read_users_me` endpoint:**
    *   Verify it correctly returns the `UserResponse` for the user identified by `get_current_user_mock`.
    *   Ensure Pydantic serialization from the SQLAlchemy model works as expected.

### 4. `echoread/api_server/routers/books.py`
*   **`_get_book_or_404` helper:**
    *   Returns correct `Book` if found for user.
    *   Raises `HTTPException` (404) if book not found.
    *   Raises `HTTPException` (404) if book belongs to another user.
*   **`_get_audio_or_404` helper:**
    *   Returns correct `Audio` if found for book and user.
    *   Raises `HTTPException` (404) if book not found (via `_get_book_or_404`).
    *   Raises `HTTPException` (404) if audio not found for that book.
*   **`upload_book` endpoint (`POST /books/upload`):**
    *   Successful upload creates a `Book` record in the DB associated with `current_user`.
    *   `_generate_and_save_audios_for_book` is called, creating associated `Audio` records in the DB.
    *   Book `status` and `chapter_count` are updated correctly.
    *   Returns `BookResponse` with correct data (202 Accepted).
    *   Test with invalid file (e.g., no filename) if applicable (though FastAPI handles some of this).
*   **`list_user_books` endpoint (`GET /books`):**
    *   Returns a list of `BookResponse` for books owned by `current_user`.
    *   Returns an empty list if `current_user` has no books.
    *   Does not return books owned by other users.
*   **`get_book_details` endpoint (`GET /books/{book_id}`):**
    *   Returns `BookDetail` (including related `AudioResponse` list) for a valid `book_id` owned by `current_user`.
    *   Returns 404 if book not found or not owned by `current_user`.
*   **`delete_book` endpoint (`DELETE /books/{book_id}`):**
    *   Successfully deletes the specified `Book` from the DB.
    *   Verify associated `Audio` records are also deleted (due to `cascade="all, delete-orphan"`).
    *   Verify associated `Play` records (with FK to this book) are also deleted (if cascade is set up for `Book->Play` or handled by DB).
    *   Returns 204 No Content on success.
    *   Returns 404 if book not found or not owned by `current_user`.
*   **`get_book_tts_status` endpoint (`GET /books/{book_id}/status`):**
    *   Returns correct `TTSStatusResponse` reflecting `book.status` and count of `book.audios`.
    *   Test for book with no audios.
    *   Test for book with some/all audios generated.
    *   Returns 404 if book not found.
*   **`list_book_audios` endpoint (`GET /books/{book_id}/audios`):**
    *   Returns list of `AudioChapterInfo` (or `AudioResponse`) for the specified book.
    *   Returns empty list if book has no audios.
    *   Returns 404 if book not found.
*   **`get_book_chapter_audio` endpoint (`GET /books/{book_id}/audios/{audio_id}`):**
    *   Returns mock MP3 data (as per current implementation) for a valid `audio_id` of a valid `book_id`.
    *   Returns 404 if book or audio not found.

### 5. `echoread/api_server/routers/plays.py`
*   **`save_play_position` endpoint (`POST /plays`):**
    *   **New Position:** If no `Play` record exists for user/book/audio, a new record is created.
    *   **Update Position:** If a `Play` record exists, its `last_timestamp` and `updated_at` are updated.
    *   Validates `book_id` and `audio_id` using helpers (implicitly tests 404 if book/audio not found).
    *   Returns `PlayResponse` with correct data.
*   **`get_last_play_position` endpoint (`GET /plays/{book_id}`):**
    *   Returns the most recently updated `PlayResponse` for the `current_user` and specified `book_id`.
    *   Returns `null` (or 404, depending on API decision for "not found optional item") if no play position exists.
    *   Correctly orders by `updated_at` if multiple play records exist for different audios of the same book.
    *   Returns 404 if book not found.

## Example Test Structure (Conceptual - using Pytest and a fixture for DB session):

```python
# conftest.py (example for setting up a test DB)
# import pytest
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession # Alias to avoid confusion
# from fastapi.testclient import TestClient

# from echoread.api_server.database import Base, get_db
# from echoread.api_server.main import app # To override dependency
# from echoread.api_server import models # To create/drop tables based on models

# # Use an in-memory SQLite database for testing
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# @pytest.fixture(scope="function")
# def db_session() -> SQLAlchemySession: # Type hint for clarity
#     Base.metadata.create_all(bind=engine) # Create tables based on models.Base
#     db = TestingSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#         Base.metadata.drop_all(bind=engine) # Drop tables after test

# @pytest.fixture(scope="function")
# def client(db_session: SQLAlchemySession): # Type hint for clarity
#     # Dependency override for get_db
#     def override_get_db():
#         try:
#             yield db_session
#         finally:
#             # Session is managed by the db_session fixture's try/finally
#             pass
#     app.dependency_overrides[get_db] = override_get_db
#     yield TestClient(app)
#     app.dependency_overrides.clear() # Clean up overrides after test


# tests/routers/test_users.py (example test file)
# from echoread.api_server import models # For DB assertions
# from datetime import datetime

# def test_read_users_me_for_new_user(client, db_session: SQLAlchemySession):
#     mock_token = "Bearer mock_jwt_token.timestamp.new_user_test@example.com"
#     response = client.get("/users/me", headers={"Authorization": mock_token})

#     assert response.status_code == 200
#     data = response.json()
#     assert data["email"] == "new_user_test@example.com"
#     assert "id" in data
#     assert "created_at" in data

#     # Verify user was actually created in the DB
#     user_in_db = db_session.query(models.User).filter(models.User.email == "new_user_test@example.com").first()
#     assert user_in_db is not None
#     assert user_in_db.id == data["id"]

# def test_read_users_me_for_existing_user(client, db_session: SQLAlchemySession):
#     # Pre-populate user in DB
#     existing_email = "existing_user_test@example.com"
#     existing_user = models.User(id="user_exists_123", email=existing_email, name="Existing User")
#     db_session.add(existing_user)
#     db_session.commit()
#     db_session.refresh(existing_user)

#     mock_token = f"Bearer mock_jwt_token.timestamp.{existing_email}"
#     response = client.get("/users/me", headers={"Authorization": mock_token})

#     assert response.status_code == 200
#     data = response.json()
#     assert data["email"] == existing_email
#     assert data["id"] == existing_user.id
#     assert data["name"] == existing_user.name
```
