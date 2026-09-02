from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


# --------------------------------------------------
# DATABASE ENGINE
# --------------------------------------------------

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)


# --------------------------------------------------
# DATABASE SESSION
# --------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# --------------------------------------------------
# BASE MODEL
# --------------------------------------------------

Base = declarative_base()


# --------------------------------------------------
# DATABASE CONNECTION TEST
# --------------------------------------------------

def check_database_connection() -> bool:
    """
    Checks whether ACCAI can successfully connect
    to the PostgreSQL database.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception:
        return False