from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Provides a SQLAlchemy database session to FastAPI endpoints.

    The session is automatically closed after the request.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()