"""Database engine, session factory and table creation."""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    connect_args = {}
    parsed = make_url(url)
    if parsed.drivername.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        # Make sure the directory for a file-backed SQLite database exists.
        if parsed.database and parsed.database != ":memory:":
            directory = os.path.dirname(os.path.abspath(parsed.database))
            os.makedirs(directory, exist_ok=True)
    return create_engine(url, connect_args=connect_args)


engine = _make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create all tables. Models must be imported so they register on Base.metadata.

    The original project failed with "no such table: users" because each model file
    declared its own `declarative_base()`, so `create_all` on the shared Base saw no tables.
    All models now inherit from the single Base above.
    """
    from . import models  # noqa: F401  (registers models)

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
