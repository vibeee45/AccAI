import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TransactionStatus


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    financial_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_periods.id", ondelete="RESTRICT"),
        nullable=False,
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    source_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    source_row_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[TransactionStatus] = mapped_column(
        SAEnum(
            TransactionStatus,
            name="transaction_status",
            native_enum=True,
        ),
        nullable=False,
        default=TransactionStatus.PENDING,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    company = relationship(
        "Company",
        back_populates="transactions",
    )

    financial_period = relationship(
        "FinancialPeriod",
        back_populates="transactions",
    )

    ai_predictions = relationship(
        "AIPrediction",
        back_populates="transaction",
    )

    corrections = relationship(
        "AICorrection",
        back_populates="transaction",
    )

    journal_entries = relationship(
        "JournalEntry",
        back_populates="transaction",
    )

    anomalies = relationship(
        "Anomaly",
        back_populates="transaction",
    )

    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
            name="ck_transactions_amount_non_negative",
        ),
        Index(
            "ix_transactions_company_date",
            "company_id",
            "transaction_date",
        ),
        Index(
            "ix_transactions_company_status",
            "company_id",
            "status",
        ),
    )