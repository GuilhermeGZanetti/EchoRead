# EchoRead: MVP Specification

DO NOT REMOVE THIS

## 1. Overview

**Title:** EchoRead
**Purpose:** A minimal mobile app to upload EPUBs, generate open‑source TTS audio, and listen on the go.

## 2. Core Features

1. **User Authentication**

   * Sign in with Google SSO

2. **EPUB Upload & Management**

   * Upload an .epub file from device
   * List user’s uploaded books

3. **TTS Generation**

   * Backend triggers a state‑of‑the‑art open‑source model (e.g., Kokoro) per chapter
   * Save audio files locally on server

4. **Audio Playback**

   * Stream generated chapters in-app
   * Play, pause, skip controls
   * Resume last position per book

## 3. Simplified Architecture

* **Mobile App:** React Native (iOS & Android)
* **API Server:** FastAPI + Uvicorn on GPU‑enabled server
* **Database:** PostgreSQL (Docker)
* **Storage:** Local filesystem for EPUBs and audio files

## 4. Data Model (MVP Tables)

* **users**: id, email, name, created\_at
* **books**: id, user\_id, title, epub\_path, created\_at
* **audios**: id, book\_id, chapter\_index, audio\_path, created\_at
* **plays**: id, user\_id, book\_id, audio\_id, last\_timestamp, updated\_at

## 5. API Endpoints (MVP)

* **POST /auth/google**

  * Exchange Google OAuth2 token for JWT.

* **POST /auth/logout**

  * Invalidate the current JWT.

* **GET /users/me**

  * Retrieve authenticated user profile.

* **POST /books/upload**

  * Upload EPUB; returns book metadata and processing status.

* **GET /books**

  * List all user books with { id, title, created\_at, status }.

* **GET /books/{book\_id}**

  * Detailed book info { id, title, author, created\_at, status, chapter\_count }.

* **DELETE /books/{book\_id}**

  * Delete book and related audio.

* **GET /books/{book\_id}/status**

  * TTS generation progress: chapters processed vs. total.

* **GET /books/{book\_id}/audios**

  * List chapter audios \[{ audio\_id, chapter\_index, url, duration }].

* **GET /books/{book\_id}/audios/{audio\_id}**

  * **Purpose:** Provide a signed URL or stream endpoint for a specific chapter audio.
  * **Auth:** `Authorization: Bearer <JWT>`.
  * **Params:** `book_id`, `audio_id` (UUIDs).
  * **Workflow:**

    1. Validate JWT and ownership.
    2. Fetch `audio_path`.
    3. Deliver via:

       * **Presigned URL** with TTL (e.g., 3600s).
       * **FastAPI Streaming** using `FileResponse` or `StreamingResponse`.
  * **Response:**

    ```json
    {
      "url": "https://api.echoread.com/media/books/{book_id}/chapters/{audio_id}.mp3?token=...",
      "expires_in": 3600
    }
    ```

* **POST /plays**

  * Save last play position { book\_id, audio\_id, last\_timestamp }.

* **GET /play/{****book\_id****}**

  * Retrieve last position for the book \[{ book\_id, audio\_id, last\_timestamp, updated\_at }].

## 6. Non-functional & Deployment. Non‑functional & Deployment. Non‑functional & Deployment

* **TTS Speed:** ≤ 30s/chapter on GPU
* **Concurrency:** Queue jobs, single‑user focus
* **Security:** HTTPS, JWT auth
* **Deploy:** Docker Compose for API + Postgres
* **Logs:** Console logs; basic error handling

---

> **App Name:** EchoRead
> A concise, memorable title reflecting instant eBook-to-audio conversion.
