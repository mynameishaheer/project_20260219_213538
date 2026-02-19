"""
Database engine, session factory, and dependency helpers.

Usage (FastAPI dependency injection):

    from src.database.database import get_db

    @app.get("/example")
    def example(db: Session = Depends(get_db)):
        ...

Environment variables:
    DATABASE_URL — Full SQLAlchemy connection URL.
                   Defaults to ``sqlite:///./app.db`` for local development.
                   Production should use ``postgresql+psycopg2://user:pass@host/db``.
"""

import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# For SQLite we enable WAL mode and foreign-key enforcement via connect hooks;
# for PostgreSQL the driver handles both natively.
_connect_args: dict = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    # Pool settings appropriate for a single-process FastAPI app.
    # Increase pool_size / max_overflow for high-concurrency deployments.
    pool_pre_ping=True,
)

# SQLite pragmas — no-op on PostgreSQL because the event only fires for SQLite
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    """
    Yield a SQLAlchemy ``Session`` and guarantee it is closed after the request.

    Intended for use with FastAPI's ``Depends()`` mechanism::

        @app.get("/")
        def route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------
def create_tables() -> None:
    """
    Create all tables defined in ``Base.metadata`` if they do not already exist.

    Safe to call on every application startup — SQLAlchemy uses
    ``CREATE TABLE IF NOT EXISTS`` semantics.  For production migrations prefer
    Alembic over calling this function directly.
    """
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """
    Drop all tables.  Intended for use in test teardown only.

    **Never call this in production code.**
    """
    Base.metadata.drop_all(bind=engine)


def health_check() -> bool:
    """
    Return True if the database is reachable, False otherwise.

    Used by the ``/health`` endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
