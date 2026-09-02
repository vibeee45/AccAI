import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CompanyRole


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    legal_name: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    financial_year_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
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

    users = relationship(
        "CompanyUser",
        back_populates="company",
    )

    financial_periods = relationship(
        "FinancialPeriod",
        back_populates="company",
    )

    accounts = relationship(
        "ChartOfAccount",
        back_populates="company",
    )

    transactions = relationship(
        "Transaction",
        back_populates="company",
    )

    journal_entries = relationship(
        "JournalEntry",
        back_populates="company",
    )

    anomalies = relationship(
        "Anomaly",
        back_populates="company",
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="company",
    )


class CompanyUser(Base):
    __tablename__ = "company_users"

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

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[CompanyRole] = mapped_column(
        SAEnum(
            CompanyRole,
            name="company_role",
            native_enum=True,
        ),
        nullable=False,
        default=CompanyRole.VIEWER,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company = relationship(
        "Company",
        back_populates="users",
    )

    user = relationship(
        "User",
        back_populates="company_memberships",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "user_id",
            name="uq_company_user",
        ),
    )