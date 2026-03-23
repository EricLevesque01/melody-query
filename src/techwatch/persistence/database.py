"""Database engine and session management."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from techwatch.config import get_settings

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _get_engine():
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
        # Enable WAL mode for SQLite for better concurrency
        if settings.database_url.startswith("sqlite"):

            @event.listens_for(_engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, _connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the session factory, creating the engine on first call."""
    global _SessionLocal  # noqa: PLW0603
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_engine(), expire_on_commit=False)
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables defined in the metadata."""
    from techwatch.persistence.tables import Base

    Base.metadata.create_all(bind=_get_engine())


def reset_engine() -> None:
    """Dispose the engine and clear singletons (useful in tests)."""
    global _engine, _SessionLocal  # noqa: PLW0603
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
