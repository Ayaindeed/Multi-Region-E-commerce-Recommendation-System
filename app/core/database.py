from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import redis
from typing import Generator

from app.core.config import settings

# Database engine
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Redis client
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    health_check_interval=30
)

def get_database() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis() -> redis.Redis:
    """Get Redis client."""
    return redis_client

def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

def close_database():
    """Close database connections."""
    engine.dispose()
