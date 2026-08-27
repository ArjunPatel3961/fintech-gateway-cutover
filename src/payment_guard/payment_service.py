from fastapi import Depends, FastAPI
from pydantic import BaseModel

from .audit_notifier import GatewayAuditNotifier
from .risk_policy import PaymentDecision, PaymentEvent, RiskAssessment, assess_payment


class PaymentOutcome(BaseModel):
    event_id: str
    assessment: RiskAssessment
    audit_notification: str | None


def notifier_dependency() -> GatewayAuditNotifier:
    return GatewayAuditNotifier()


service = FastAPI(title="Payment gateway cutover")


@service.post("/payments/decide", response_model=PaymentOutcome)
def decide_payment(
    event: PaymentEvent,
    notifier: GatewayAuditNotifier = Depends(notifier_dependency),
) -> PaymentOutcome:
    assessment = assess_payment(event)
    notification = None
    if assessment.decision is not PaymentDecision.RELEASE:
        notification = notifier.write(event, assessment)
    return PaymentOutcome(
        event_id=event.event_id,
        assessment=assessment,
        audit_notification=notification,
    )
