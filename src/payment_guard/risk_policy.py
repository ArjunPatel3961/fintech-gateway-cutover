from enum import Enum

from pydantic import BaseModel, Field


class RiskSignal(str, Enum):
    NONE = "none"
    VELOCITY = "velocity"
    ACCOUNT_TAKEOVER = "account_takeover"


class PaymentEvent(BaseModel):
    event_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    amount_minor: int = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    risk_signal: RiskSignal = RiskSignal.NONE


class PaymentDecision(str, Enum):
    RELEASE = "release"
    REVIEW = "review"
    BLOCK = "block"


class RiskAssessment(BaseModel):
    decision: PaymentDecision
    reason: str


def assess_payment(event: PaymentEvent) -> RiskAssessment:
    """Keep the business decision deterministic and separate from AI wording."""
    if event.risk_signal is RiskSignal.ACCOUNT_TAKEOVER:
        return RiskAssessment(decision=PaymentDecision.BLOCK, reason="account_takeover_signal")
    if event.risk_signal is RiskSignal.VELOCITY or event.amount_minor >= 1_000_000:
        return RiskAssessment(decision=PaymentDecision.REVIEW, reason="manual_review_threshold")
    return RiskAssessment(decision=PaymentDecision.RELEASE, reason="policy_checks_passed")
