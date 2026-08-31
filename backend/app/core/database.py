from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
# Engine/session configuration will be finalized in Phase 1.
engine = None
SessionLocal = sessionmaker()
