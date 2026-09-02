import pytest

from app.core.database import Base, SessionLocal

# Import all models so SQLAlchemy knows about every table
from app.models.user import User
from app.models.company import Company, CompanyUser
from app.models.financial_period import FinancialPeriod
from app.models.account import ChartOfAccount
from app.models.transaction import Transaction
from app.models.journal import JournalEntry, JournalLine
from app.models.ai_prediction import AIPrediction
from app.models.correction import AICorrection
from app.models.anomaly import Anomaly
from app.models.audit_log import AuditLog


@pytest.fixture
def db():
    """
    Provide a fresh database session for every test.

    Each test is allowed to commit normally because the application
    services use db.commit() internally.

    After the test finishes, all database tables are cleaned so that
    the next test starts with an empty database.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        # Make sure the session is not left in a failed transaction state.
        db.rollback()

        # Delete all rows from all tables in reverse dependency order.
        #
        # Base.metadata.sorted_tables gives SQLAlchemy's dependency-aware
        # table ordering. Reversing it means child tables are deleted
        # before parent tables.
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())

        db.commit()
        db.close()