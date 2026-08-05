import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.config import settings

logger = logging.getLogger("codesage.database")

db_url = settings.DATABASE_URL
connect_args = {}
engine_kwargs = {"pool_pre_ping": True}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Production PostgreSQL connection pool tuning
    engine_kwargs.update({
        "pool_size": 15,
        "max_overflow": 20,
        "pool_recycle": 1800,
    })

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db() -> None:
    """Helper creating all defined tables in the configured database engine."""
    try:
        import app.models.db  # Ensure all ORM models are registered
        Base.metadata.create_all(bind=engine)
        logger.info(f"Initialized database schema on {db_url}.")
    except Exception as e:
        logger.warning(f"Database initialization warning on {db_url}: {e}")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a thread-safe database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
