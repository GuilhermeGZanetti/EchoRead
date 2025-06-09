from fastapi import FastAPI

# Import the routers
from echoread.api_server.routers import auth, users, books, plays # Relative imports for routers

app = FastAPI(
    title="EchoRead API",
    description="API for EchoRead mobile application, including TTS generation from EPUBs.",
    version="0.1.0"
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to EchoRead API"}

# Include the routers in the app
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(books.router)
app.include_router(plays.router)

# To run this app (save as main.py in api_server directory):
# Ensure you are in the 'echoread' directory (one level above api_server)
# Then run: uvicorn api_server.main:app --reload --port 8000
