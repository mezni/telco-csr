from enum import Enum

from pydantic import BaseModel, Field


class TelecomIntent(str, Enum):
    BILLING_SPIKE = "BILLING_SPIKE"
    CREDIT_REQUEST = "CREDIT_REQUEST"
    PAYMENT_EXTENSION = "PAYMENT_EXTENSION"
    PLAN_CHANGE = "PLAN_CHANGE"
    GENERAL_FAQ = "GENERAL_FAQ"
    UNKNOWN = "UNKNOWN"


class IntentClassification(BaseModel):
    intent: TelecomIntent = Field(
        description=(
            "Primary telecom operational intent extracted from the customer query."
        )
    )
    confidence: float = Field(
        description=(
            "Confidence score between 0.0 and 1.0 representing "
            "classification certainty."
        ),
        ge=0.0,
        le=1.0,
    )
    reasoning: str = Field(
        description="Brief justification for why this intent was selected."
    )
