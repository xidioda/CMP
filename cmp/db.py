from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from .config import settings

Base = declarative_base()


def _get_default_sqlite_url() -> str:
    # Local, zero-config default
    return "sqlite+pysqlite:///cmp.db"


def _make_engine(url: str | None):
    url = url or _get_default_sqlite_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite+") else {}
    return create_engine(url, echo=False, future=True, connect_args=connect_args)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True, expire_on_commit=False)


def init_db() -> None:
    # Import models so they are registered with Base
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# FastAPI dependency

def get_db() -> Iterator[Session]:
    with session_scope() as s:
        yield s
