# EchoRead

## Purpose

EchoRead is a minimal mobile application designed to allow users to upload EPUB files, generate text-to-speech (TTS) audio from them using open-source models, and listen to the generated audio on the go.

## Core Features

*   **User Authentication:**
    *   Sign in with Google SSO.
*   **EPUB Upload & Management:**
    *   Upload `.epub` files from the user's device.
    *   List all books uploaded by the user.
*   **TTS Generation:**
    *   The backend processes each chapter of an EPUB using a state-of-the-art open-source TTS model (e.g., Kokoro).
    *   Generated audio files are saved locally on the server.
*   **Audio Playback:**
    *   Stream generated audio chapters within the app.
    *   Standard playback controls: play, pause, skip.
    *   Resume playback from the last position for each book.

## Simplified Architecture

*   **Mobile App:** React Native (iOS & Android)
*   **API Server:** FastAPI + Uvicorn, running on a GPU-enabled server.
*   **Database:** PostgreSQL (managed with Docker).
*   **Storage:** Local filesystem for storing EPUB files and generated audio files.

## Project Structure

```
echoread/
├── api_server/           # FastAPI backend
│   ├── main.py           # FastAPI app initialization
│   ├── models.py         # SQLAlchemy data models
│   ├── routers/          # API endpoint routers
│   │   ├── __init__.py
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── users.py      # User-related endpoints
│   │   ├── books.py      # Book and audio-related endpoints
│   │   └── plays.py      # Playback status endpoints
│   └── Dockerfile        # Dockerfile for the API server
├── database/             # PostgreSQL setup
│   └── init.sql          # Initial database schema
├── mobile_app/           # React Native application
│   └── App.js            # Main application component (placeholder)
├── docker-compose.yml    # Docker Compose configuration
└── README.md             # This file
```

## Installation

To set up and run EchoRead, you'll use Docker Compose. This will build the necessary Docker images and start the services (API server and database).

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd echoread
    ```
2.  **Build and run the services:**
    Execute the following command from the root of the `echoread` directory:
    ```bash
    docker-compose up -d --build
    ```
    This command will:
    *   Build the Docker image for the `api_server` if it doesn't exist or if changes have been made to its Dockerfile or context.
    *   Start all services defined in `docker-compose.yml` in detached mode (`-d`).
    *   The API server will be available at `http://localhost:8000`.

## Development

For development, the `api_server` is configured for live reloading. This means that any changes you make to the Python code within the `api_server` directory on your local machine will automatically trigger a reload of the server within the Docker container.

*   **Live Reload:** The `api` service in `docker-compose.yml` uses the `uvicorn --reload` command.
*   **Volume Mounting:** The `api_server` directory is mounted as a volume into the container. This ensures that your local code changes are directly reflected inside the container, allowing Uvicorn to detect them and reload.

To run in development mode, use the same command as for installation:
```bash
docker-compose up -d --build
```
You can then view the logs for the API server to see the reload messages:
```bash
docker-compose logs -f api
```

## Data Model (MVP Tables)

*   **users:** `id`, `email`, `name`, `created_at`
*   **books:** `id`, `user_id`, `title`, `epub_path`, `created_at`
*   **audios:** `id`, `book_id`, `chapter_index`, `audio_path`, `created_at`
*   **plays:** `id`, `user_id`, `book_id`, `audio_id`, `last_timestamp`, `updated_at`

## API Endpoints (MVP)

*   `POST /auth/google`: Exchange Google OAuth2 token for JWT.
*   `POST /auth/logout`: Invalidate the current JWT.
*   `GET /users/me`: Retrieve authenticated user profile.
*   `POST /books/upload`: Upload EPUB; returns book metadata and processing status.
*   `GET /books`: List all user books with `{ id, title, created_at, status }`.
*   `GET /books/{book_id}`: Detailed book info `{ id, title, author, created_at, status, chapter_count }`.
*   `DELETE /books/{book_id}`: Delete book and related audio.
*   `GET /books/{book_id}/status`: TTS generation progress: chapters processed vs. total.
*   `GET /books/{book_id}/audios`: List chapter audios `[{ audio_id, chapter_index, url, duration }]`.
*   `GET /books/{book_id}/audios/{audio_id}`: Provide a signed URL or stream endpoint for a specific chapter audio.
*   `POST /plays`: Save last play position `{ book_id, audio_id, last_timestamp }`.
*   `GET /play/{book_id}`: Retrieve last position for the book `[{ book_id, audio_id, last_timestamp, updated_at }]`.

## Non-functional & Deployment

*   **TTS Speed:** Target ≤ 30 seconds per chapter on GPU.
*   **Concurrency:** Job queue for TTS tasks, initially focused on a single-user experience.
*   **Security:** HTTPS for all communications, JWT for authentication.
*   **Deployment:** Docker Compose to manage the API server and PostgreSQL database.
*   **Logs:** Console logs with basic error handling.
```
