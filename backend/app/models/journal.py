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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import JournalStatus


class JournalEntry(Base):
    __tablename__ = "journal_entries"

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

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="RESTRICT"),
        nullable=False,
    )

    entry_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    entry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[JournalStatus] = mapped_column(
        SAEnum(
            JournalStatus,
            name="journal_status",
            native_enum=True,
        ),
        nullable=False,
        default=JournalStatus.DRAFT,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company = relationship(
        "Company",
        back_populates="journal_entries",
    )

    transaction = relationship(
        "Transaction",
        back_populates="journal_entries",
    )

    lines = relationship(
        "JournalLine",
        back_populates="journal_entry",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "entry_number",
            name="uq_journal_entries_company_entry_number",
        ),
        Index(
            "ix_journal_entries_company_date",
            "company_id",
            "entry_date",
        ),
    )


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    debit: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    credit: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    line_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    journal_entry = relationship(
        "JournalEntry",
        back_populates="lines",
    )

    account = relationship(
        "ChartOfAccount",
        back_populates="journal_lines",
    )

    __table_args__ = (
        CheckConstraint(
            "debit >= 0",
            name="ck_journal_lines_debit_non_negative",
        ),
        CheckConstraint(
            "credit >= 0",
            name="ck_journal_lines_credit_non_negative",
        ),
        CheckConstraint(
            "(debit > 0 AND credit = 0) OR "
            "(credit > 0 AND debit = 0)",
            name="ck_journal_lines_one_side_only",
        ),
        Index(
            "ix_journal_lines_account",
            "account_id",
        ),
        Index(
            "ix_journal_lines_journal_entry",
            "journal_entry_id",
        ),
    )