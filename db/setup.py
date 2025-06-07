import os
import asyncio
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session
from typing import Generator, Dict, Any
from sqlalchemy.ext.automap import automap_base

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,   # Recycle connections every hour
    pool_size=10,        # Number of connections to maintain
    max_overflow=20,     # Additional connections when needed
    echo=False           # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use automap_base for reflection
Base = automap_base()
Base.prepare(autoload_with=engine)

# Function to get a database session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()