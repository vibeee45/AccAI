import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AccountType, NormalBalance


class ChartOfAccount(Base):
    __tablename__ = "chart_of_accounts"

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

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    account_type: Mapped[AccountType] = mapped_column(
        SAEnum(
            AccountType,
            name="account_type",
            native_enum=True,
        ),
        nullable=False,
    )

    normal_balance: Mapped[NormalBalance] = mapped_column(
        SAEnum(
            NormalBalance,
            name="normal_balance",
            native_enum=True,
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company = relationship(
        "Company",
        back_populates="accounts",
    )

    parent = relationship(
        "ChartOfAccount",
        remote_side="ChartOfAccount.id",
        back_populates="children",
    )

    children = relationship(
        "ChartOfAccount",
        back_populates="parent",
    )

    journal_lines = relationship(
        "JournalLine",
        back_populates="account",
    )

    ai_debit_predictions = relationship(
        "AIPrediction",
        foreign_keys="AIPrediction.debit_account_id",
        back_populates="debit_account",
    )

    ai_credit_predictions = relationship(
        "AIPrediction",
        foreign_keys="AIPrediction.credit_account_id",
        back_populates="credit_account",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_chart_of_accounts_company_code",
        ),
        Index(
            "ix_chart_of_accounts_company_type",
            "company_id",
            "account_type",
        ),
    )