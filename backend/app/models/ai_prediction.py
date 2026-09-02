import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    debit_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=True,
    )

    credit_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"),
        nullable=True,
    )

    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    prediction_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    transaction = relationship(
        "Transaction",
        back_populates="ai_predictions",
    )

    debit_account = relationship(
        "ChartOfAccount",
        foreign_keys=[debit_account_id],
        back_populates="ai_debit_predictions",
    )

    credit_account = relationship(
        "ChartOfAccount",
        foreign_keys=[credit_account_id],
        back_populates="ai_credit_predictions",
    )

    corrections = relationship(
        "AICorrection",
        back_populates="prediction",
    )

    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_ai_predictions_confidence_range",
        ),
        Index(
            "ix_ai_predictions_transaction",
            "transaction_id",
        ),
    )