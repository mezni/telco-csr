from enum import Enum

from pydantic import BaseModel, Field


# 1. Define the enum for telecom intents
class TelecomIntent(str, Enum):
    BILLING_INQUIRY = "billing_inquiry"
    TECHNICAL_SUPPORT = "technical_support"
    PLAN_UPGRADE = "plan_upgrade"
    CANCELLATION = "cancellation"
    SIM_ACTIVATION = "sim_activation"


# 2. Your IntentClassification model
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
