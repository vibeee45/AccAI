from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AnomalyStatus, RiskLevel


class AnomalyResponse(BaseModel):
    id: UUID
    company_id: UUID
    transaction_id: UUID
    model_version: str
    anomaly_score: Decimal
    risk_level: RiskLevel
    explanation: str | None
    status: AnomalyStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyUpdate(BaseModel):
    status: AnomalyStatus