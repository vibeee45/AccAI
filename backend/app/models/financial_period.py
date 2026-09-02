import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import FinancialPeriodStatus


class FinancialPeriod(Base):
    __tablename__ = "financial_periods"

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

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[FinancialPeriodStatus] = mapped_column(
        SAEnum(
            FinancialPeriodStatus,
            name="financial_period_status",
            native_enum=True,
        ),
        nullable=False,
        default=FinancialPeriodStatus.OPEN,
    )

    company = relationship(
        "Company",
        back_populates="financial_periods",
    )

    transactions = relationship(
        "Transaction",
        back_populates="financial_period",
    )

    __table_args__ = (
        Index(
            "ix_financial_periods_company_dates",
            "company_id",
            "start_date",
            "end_date",
        ),
    )