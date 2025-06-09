from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from dev.env, which should be in the same directory
# as this file or the main application entry point.
# Assuming dev.env is in api_server, and this script is also in api_server.
dotenv_path = os.path.join(os.path.dirname(__file__), 'dev.env')
load_dotenv(dotenv_path=dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # This will halt startup if dev.env is missing or DATABASE_URL is not in it.
    raise RuntimeError("DATABASE_URL environment variable not set. Ensure dev.env is present and configured correctly in echoread/api_server/dev.env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
