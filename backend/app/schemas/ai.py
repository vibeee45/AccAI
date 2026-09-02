from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AIPredictionResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    model_version: str
    transaction_type: str
    debit_account_id: UUID | None
    credit_account_id: UUID | None
    confidence: Decimal = Field(ge=0, le=1)
    prediction_payload: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AICorrectionCreate(BaseModel):
    transaction_id: UUID
    prediction_id: UUID
    user_id: UUID
    original_prediction: dict[str, Any]
    corrected_prediction: dict[str, Any]
    reason: str | None = Field(default=None, max_length=2000)


class AICorrectionResponse(AICorrectionCreate):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)