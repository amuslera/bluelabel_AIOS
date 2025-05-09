# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
import logging

from app.core.config_file import settings
from app.db.schema import Base

logger = logging.getLogger(__name__)

def get_engine():
    """Get SQLAlchemy engine"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Create database if it doesn't exist
    if not database_exists(engine.url):
        logger.info(f"Creating database at {settings.DATABASE_URL}")
        create_database(engine.url)
    
    return engine

def create_tables():
    """Create all tables if they don't exist"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

def get_session_maker():
    """Get a session maker for database operations"""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create SessionLocal class
SessionLocal = get_session_maker()

def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()