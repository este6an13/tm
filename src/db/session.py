from os.path import abspath, dirname

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import (  # noqa: F401
    Base,
    Counts,
    NetworkEdge,
    NetworkNode,
    ProcessedFile,
    Station,
)
from src.utils.logging import logger

BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
DATABASE_FILE = "tm.db"
DATABASE_URL = "sqlite:///" / BASE_DIR / DATABASE_FILE

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_database():
    """Drops and recreates all tables."""
    logger.info("Starting database reset...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.clear()
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset complete.")
