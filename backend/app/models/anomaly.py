import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AnomalyStatus, RiskLevel


class Anomaly(Base):
    __tablename__ = "anomalies"

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
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    anomaly_score: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        nullable=False,
    )

    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(
            RiskLevel,
            name="risk_level",
            native_enum=True,
        ),
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[AnomalyStatus] = mapped_column(
        SAEnum(
            AnomalyStatus,
            name="anomaly_status",
            native_enum=True,
        ),
        nullable=False,
        default=AnomalyStatus.OPEN,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company = relationship(
        "Company",
        back_populates="anomalies",
    )

    transaction = relationship(
        "Transaction",
        back_populates="anomalies",
    )

    __table_args__ = (
        Index(
            "ix_anomalies_company_risk",
            "company_id",
            "risk_level",
        ),
    )